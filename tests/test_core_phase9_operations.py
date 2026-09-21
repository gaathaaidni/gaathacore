import os

import pytest

from core.config import CoreDatabaseConfig
from core.factory import create_core_service
from core.operations import core_health
from core.postgres import PostgresCoreService


DATABASE_URL = os.environ.get("CORE_DATABASE_URL")


def test_invalid_configuration_is_non_sensitive_and_not_ready(monkeypatch):
    monkeypatch.delenv("CORE_DATABASE_URL", raising=False)
    monkeypatch.setenv("CORE_ENV", "staging")
    health = core_health()
    assert health["status"] == "not_ready"
    assert health["configuration"]["status"] == "invalid"
    assert "password" not in str(health).lower()

    with pytest.raises(RuntimeError, match="complete PostgreSQL URL"):
        CoreDatabaseConfig.from_values("postgresql://localhost", "staging")


def test_staging_factory_rejects_sqlite(monkeypatch):
    monkeypatch.delenv("CORE_DATABASE_URL", raising=False)
    monkeypatch.setenv("CORE_ENV", "staging")
    with pytest.raises(RuntimeError, match="required in staging"):
        create_core_service()


@pytest.mark.skipif(not DATABASE_URL, reason="CORE_DATABASE_URL is required for PostgreSQL operational tests")
def test_postgres_health_migration_and_transaction_behavior():
    from core.migrations.runner import CoreMigrationRunner
    import psycopg2

    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")

    before = core_health(database_url=DATABASE_URL)
    assert before["status"] == "not_ready"
    assert before["database"]["status"] == "reachable"
    assert before["migrations"]["status"] == "not_initialized"

    CoreMigrationRunner(DATABASE_URL).upgrade()
    after = core_health(database_url=DATABASE_URL)
    assert after["status"] == "ready"
    assert after["migrations"] == {"status": "current", "head": "001", "pending": []}

    service = PostgresCoreService(DATABASE_URL, migrate=False)
    user = service.create_user(email="phase9-owner@example.com", username="phase9-owner")
    with pytest.raises(Exception):
        service.create_user(email="phase9-owner@example.com", username="phase9-other")
    recovered = service.create_user(email="phase9-recovered@example.com", username="phase9-recovered")
    assert user["id"] != recovered["id"]


@pytest.mark.skipif(not DATABASE_URL, reason="CORE_DATABASE_URL is required for PostgreSQL operational tests")
def test_unavailable_database_is_not_ready():
    health = core_health(database_url="postgresql://invalid:invalid@127.0.0.1:1/gaathacore_core")
    assert health["status"] == "not_ready"
    assert health["database"]["status"] == "unreachable"
    assert "invalid" not in str(health.get("database", {})).lower()