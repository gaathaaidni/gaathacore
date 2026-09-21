from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class CoreDatabaseConfig:
    database_url: str
    environment: str

    @classmethod
    def from_environment(cls) -> "CoreDatabaseConfig":
        database_url = os.environ.get("CORE_DATABASE_URL", "").strip()
        environment = os.environ.get("CORE_ENV", os.environ.get("APP_ENV", os.environ.get("FLASK_ENV", "development"))).strip().lower()
        return cls.from_values(database_url, environment)

    @classmethod
    def from_values(cls, database_url: str, environment: str) -> "CoreDatabaseConfig":
        database_url = (database_url or "").strip()
        environment = (environment or "").strip().lower()
        if environment not in {"development", "test", "staging", "production"}:
            raise RuntimeError("CORE_ENV must be development, test, staging, or production")
        if not database_url:
            raise RuntimeError("CORE_DATABASE_URL is required for the PostgreSQL Core database")
        parsed = urlparse(database_url)
        if parsed.scheme.lower() not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
            raise RuntimeError("CORE_DATABASE_URL must be a complete PostgreSQL URL")
        return cls(database_url=database_url, environment=environment)


def core_database_url() -> str:
    return CoreDatabaseConfig.from_environment().database_url