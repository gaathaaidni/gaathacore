from __future__ import annotations

from typing import Any, Dict, Optional

import psycopg2

from core.config import CoreDatabaseConfig
from core.migrations.runner import CoreMigrationRunner


def core_health(*, database_url: Optional[str] = None) -> Dict[str, Any]:
    """Return non-sensitive process, configuration, database, and schema state."""
    try:
        config = CoreDatabaseConfig.from_values(database_url, "staging") if database_url else CoreDatabaseConfig.from_environment()
    except (RuntimeError, TypeError, ValueError) as exc:
        return {
            "status": "not_ready",
            "process": "available",
            "configuration": {"status": "invalid", "error": str(exc)},
            "database": {"status": "not_checked"},
            "migrations": {"status": "not_checked"},
            "schema": {"status": "not_checked"},
        }

    try:
        with psycopg2.connect(config.database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.execute("SELECT to_regclass('public.core_schema_migrations')")
                history_table = cursor.fetchone()[0]
        if history_table is None:
            return {
                "status": "not_ready",
                "process": "available",
                "configuration": {"status": "valid", "environment": config.environment},
                "database": {"status": "reachable"},
                "migrations": {"status": "not_initialized"},
                "schema": {"status": "not_ready"},
            }
        migration_status = CoreMigrationRunner(config.database_url).status(create_history=False)
        ready = not migration_status["pending"]
        return {
            "status": "ready" if ready else "not_ready",
            "process": "available",
            "configuration": {"status": "valid", "environment": config.environment},
            "database": {"status": "reachable"},
            "migrations": {"status": "current" if ready else "pending", "head": migration_status["head"], "pending": migration_status["pending"]},
            "schema": {"status": "ready" if ready else "not_ready"},
        }
    except psycopg2.Error:
        return {
            "status": "not_ready",
            "process": "available",
            "configuration": {"status": "valid", "environment": config.environment},
            "database": {"status": "unreachable"},
            "migrations": {"status": "not_checked"},
            "schema": {"status": "not_ready"},
        }