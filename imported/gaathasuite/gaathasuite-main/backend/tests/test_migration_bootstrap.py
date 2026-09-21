import os
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from conftest import get_test_sync_database_url


requires_test_database = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL must point to an isolated PostgreSQL database",
)


CORE_TABLES = {
    "organizations",
    "users",
    "customers",
    "leads",
    "opportunities",
    "invoice",
    "invoice_line",
    "vendors",
    "purchase_orders",
    "expenses",
    "items",
    "warehouse",
    "stock_record",
    "stock_transaction",
    "attendance_record",
    "employee",
    "payslip",
    "performance_review",
    "notifications",
    "notification_preferences",
    "legal_documents",
    "legal_acceptances",
    "settings_change_log",
}


def test_bootstrap_contract_matches_runtime_metadata():
    from app import models  # noqa: F401
    from app.db import Base

    migration_path = Path(__file__).parents[1] / "migrations" / "versions" / (
        "303fea8f86b8_reconcile_fastapi_model_schema.py"
    )
    spec = importlib.util.spec_from_file_location("reconcile_303", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert set(migration.REQUIRED_TABLES) <= set(Base.metadata.tables)
    assert not set(migration.REQUIRED_TABLES) & {
        "activity_log",
        "asset",
        "coupon",
        "hr_employees",
    }


@pytest.fixture
def migrated_database():
    engine = create_engine(get_test_sync_database_url())
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "migrations/alembic.ini", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=os.environ.copy(),
        check=True,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@requires_test_database
def test_fresh_database_reaches_current_head(migrated_database):
    inspector = inspect(migrated_database)
    assert CORE_TABLES <= set(inspector.get_table_names())

    with migrated_database.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "20260922_journal_immutability"


@requires_test_database
def test_fresh_database_preserves_schema_contracts(migrated_database):
    inspector = inspect(migrated_database)

    assert any(
        foreign_key["referred_table"] == "organizations"
        for foreign_key in inspector.get_foreign_keys("users")
    )
    assert any(
        foreign_key["referred_table"] == "users"
        for foreign_key in inspector.get_foreign_keys("notification_preferences")
    )
    assert any(
        constraint["name"] == "uq_legal_acceptance_version"
        for constraint in inspector.get_unique_constraints("legal_acceptances")
    )
    assert any(
        index["name"] == "ix_users_email" and index["unique"]
        for index in inspector.get_indexes("users")
    )
    assert any(
        index["name"] == "ix_purchase_orders_reference_number" and index["unique"]
        for index in inspector.get_indexes("purchase_orders")
    )


def test_legacy_compatibility_drift_is_excluded_but_canonical_drift_is_detected():
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.utils.migration_comparison import include_name, include_object
    from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

    metadata = MetaData()
    legacy_tables = {
        "department",
        "invoice",
        "invoice_line",
        "invoice_sequence",
        "notification_preferences",
    }
    for table_name in legacy_tables:
        Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True),
            Column("model_value", String),
        )
    Table(
        "canonical_table",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("required_name", String),
    )

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        for table_name in legacy_tables:
            connection.exec_driver_sql(
                f"CREATE TABLE {table_name} "
                "(id INTEGER PRIMARY KEY, legacy_value TEXT, changed TEXT)"
            )
        connection.exec_driver_sql(
            "CREATE TABLE canonical_table (id INTEGER PRIMARY KEY)"
        )
        context = MigrationContext.configure(
            connection,
            opts={
                "target_metadata": metadata,
                "include_name": include_name,
                "include_object": include_object,
                "compare_nullable": False,
                "compare_type": False,
            },
        )
        differences = compare_metadata(context, metadata)

    assert any(
        difference[0] == "add_column"
        and difference[2] == "canonical_table"
        and difference[3].name == "required_name"
        for difference in differences
    )
    assert not any(
        any(table_name in repr(difference) for table_name in legacy_tables)
        for difference in differences
    )
