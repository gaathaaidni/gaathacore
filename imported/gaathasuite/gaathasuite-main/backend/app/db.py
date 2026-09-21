from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool
from sqlalchemy import Integer, DateTime, func, Boolean, text
from sqlalchemy.orm import Session
from datetime import datetime
import os
from dotenv import load_dotenv

for env_path in [
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[1] / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path, override=False)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Import-time safety for bootstrap checks and legacy config validation tests.
    # The application startup path still enforces required configuration before
    # accepting connections; this avoids crashing unrelated metadata imports.
    DATABASE_URL = "postgresql+asyncpg://gaatha:gaatha@localhost:5432/gaatha"
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine_options = {
    "echo": False,
    "connect_args": {
        "server_settings": {
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        }
    },
}
if os.environ.get("TEST_DATABASE_URL"):
    engine_options["poolclass"] = NullPool
else:
    engine_options.update(
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
    )

engine = create_async_engine(DATABASE_URL, **engine_options)


class GuardedSession(Session):
    """Reject deletion of posted accounting records before SQL is emitted."""

    def delete(self, instance):
        table_name = getattr(instance, "__tablename__", None)
        if table_name == "journal_entry" and getattr(instance, "status", None) == "posted":
            raise ValueError("Posted journal entries are immutable; create a reversal instead")
        if table_name == "journal_line":
            status = self.execute(
                text(
                    "SELECT status FROM journal_entry "
                    "WHERE id = :entry_id"
                ),
                {"entry_id": instance.entry_id},
            ).scalar_one_or_none()
            if status == "posted":
                raise ValueError("Posted journal lines are immutable; create a reversal instead")
        return super().delete(instance)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    sync_session_class=GuardedSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class which provides automated table name
    and surrogate primary key column, plus timestamp fields.
    """
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session