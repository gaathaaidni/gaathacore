import asyncio
import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


TEST_DATABASE_NAME = os.environ.get("TEST_DATABASE_NAME", "gaatha_migration_test")


def _test_database_urls():
    sync_url = os.environ.get("TEST_DATABASE_URL")
    if not sync_url:
        return None, None

    sync_database_url = make_url(sync_url)
    if sync_database_url.drivername != "postgresql+psycopg2":
        raise pytest.UsageError(
            "TEST_DATABASE_URL must use postgresql+psycopg2:// for synchronous test helpers"
        )
    if sync_database_url.database != TEST_DATABASE_NAME:
        raise pytest.UsageError(
            f"TEST_DATABASE_URL must target the isolated {TEST_DATABASE_NAME!r} database"
        )

    async_url = os.environ.get("TEST_ASYNC_DATABASE_URL")
    async_database_url = make_url(async_url) if async_url else sync_database_url.set(
        drivername="postgresql+asyncpg"
    )
    if async_database_url.drivername != "postgresql+asyncpg":
        raise pytest.UsageError(
            "TEST_ASYNC_DATABASE_URL must use postgresql+asyncpg:// for the application"
        )
    if async_database_url.database != sync_database_url.database:
        raise pytest.UsageError(
            "TEST_ASYNC_DATABASE_URL and TEST_DATABASE_URL must target the same database"
        )
    for component in ("host", "port", "username"):
        if getattr(async_database_url, component) != getattr(sync_database_url, component):
            raise pytest.UsageError(
                "TEST_ASYNC_DATABASE_URL and TEST_DATABASE_URL must target the same server"
            )

    return async_database_url, sync_database_url


TEST_ASYNC_URL, TEST_SYNC_URL = _test_database_urls()
if TEST_ASYNC_URL is not None:
    # Configure this before test modules can import app.db or app.main.
    os.environ["TEST_ASYNC_DATABASE_URL"] = TEST_ASYNC_URL.render_as_string(hide_password=False)
    os.environ["DATABASE_URL"] = os.environ["TEST_ASYNC_DATABASE_URL"]
    os.environ["SECRET_KEY"] = "test-only-secret-that-is-not-production"


def get_test_async_database_url():
    if TEST_ASYNC_URL is None:
        raise pytest.UsageError("TEST_DATABASE_URL is required for database-backed tests")
    return TEST_ASYNC_URL.render_as_string(hide_password=False)


def get_test_sync_database_url():
    if TEST_SYNC_URL is None:
        raise pytest.UsageError("TEST_DATABASE_URL is required for database-backed tests")
    return TEST_SYNC_URL.render_as_string(hide_password=False)


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient

    from app.db import AsyncSessionLocal, engine
    from app.main import app
    from app.utils.dependencies import get_db

    with create_engine(get_test_sync_database_url()).begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "migrations/alembic.ini", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=os.environ.copy(),
        check=True,
    )

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())