from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from app.models.base import Base
from app.utils.roles import canonical_role, ROLE_ORGADMIN, ROLE_SUPERADMIN, ROLE_STANDARD_USER, ROLE_USER

class User(Base):
    """User account model with role-based access control."""
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str] = mapped_column(String(80), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default=ROLE_USER)  # user, orgadmin, manager, auditor, partner, superadmin
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    department: Mapped[str] = mapped_column(String(200), nullable=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # OAuth
    oauth_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    oauth_provider: Mapped[str] = mapped_column(String(50), nullable=True)  # google, microsoft, etc
    
    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    otps: Mapped[list["OTP"]] = relationship(back_populates="user")
    assets: Mapped[list["Asset"]] = relationship(
        "app.models.asset.Asset", back_populates="assigned_to"
    )
    # Legacy duplicate asset definitions remain in the codebase for compatibility,
    # but the authoritative runtime model is app.models.asset.Asset.

    def set_password(self, password: str):
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self) -> bool:
        role = canonical_role(self.role)
        return role in {ROLE_ORGADMIN, ROLE_SUPERADMIN}

    @property
    def is_superadmin(self) -> bool:
        return canonical_role(self.role) == ROLE_SUPERADMIN

    @property
    def is_orgadmin(self) -> bool:
        return canonical_role(self.role) == ROLE_ORGADMIN

    @property
    def last_login(self):
        return self.last_login_at

    def __repr__(self):
        return f'<User {self.email}>'


class APIKey(Base):
    __tablename__ = 'api_keys'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="api_keys")


class OTP(Base):
    __tablename__ = 'otps'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow() + timedelta(minutes=5))
    
    user: Mapped["User"] = relationship(back_populates="otps")


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")