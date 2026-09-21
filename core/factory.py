from __future__ import annotations

import os

from core.config import core_database_url
from core.platform import GaathaCoreService
from core.postgres import PostgresCoreService


def create_core_service(*, database_path: str | None = None):
    """Create the canonical Core service, with SQLite explicit for local tests only."""
    if os.environ.get("CORE_DATABASE_URL"):
        return PostgresCoreService(core_database_url())
    environment = os.environ.get("CORE_ENV", os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))).lower()
    if environment not in {"development", "test", "staging", "production"}:
        raise RuntimeError("CORE_ENV must be development, test, staging, or production")
    if environment in {"staging", "production"}:
        raise RuntimeError("CORE_DATABASE_URL is required in staging and production; SQLite is test/dev only")
    return GaathaCoreService(database_path=database_path or os.environ.get("GAATHACORE_DB_PATH", "gaathacore.db"))