import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext


MIGRATION_PATH = Path(__file__).parents[1] / "migrations" / "versions" / "009_inventory_foundation.py"


def load_migration():
    spec = importlib.util.spec_from_file_location("migration_009", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def run_migration(connection, operation):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        operation()


def test_inventory_foundation_migration_preserves_and_owns_legacy_inventory():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("restaurant", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("user", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "inventory_item",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=True),
    )
    sa.Table(
        "product",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("restaurant_id", sa.Integer, nullable=False),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(sa.text("PRAGMA foreign_keys = ON"))
        connection.execute(sa.text("INSERT INTO restaurant (id) VALUES (1)"))
        connection.execute(
            sa.text("INSERT INTO inventory_item (id, name, quantity) VALUES (1, 'Oil', 5)")
        )
        connection.execute(sa.text("INSERT INTO product (id, restaurant_id) VALUES (1, 1)"))
        migration = load_migration()
        run_migration(connection, migration.upgrade)

        row = connection.execute(
            sa.text("SELECT id, restaurant_id, quantity FROM inventory_item")
        ).one()
        assert row == (1, 1, 5)
        assert sa.inspect(connection).has_table("product_recipe")
        assert sa.inspect(connection).has_table("inventory_movement")

        with pytest.raises(RuntimeError):
            run_migration(connection, migration.downgrade)


def test_migration_preserves_orphaned_inventory_and_rejects_unsafe_ownership_assignment():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("restaurant", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("user", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "inventory_item",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=True),
        sa.Column("restaurant_id", sa.Integer, nullable=True),
    )
    sa.Table(
        "product",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("restaurant_id", sa.Integer, nullable=False),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(sa.text("PRAGMA foreign_keys = ON"))
        connection.execute(sa.text("INSERT INTO restaurant (id) VALUES (1), (2)"))
        connection.execute(
            sa.text("INSERT INTO inventory_item (id, name, quantity, restaurant_id) VALUES (1, 'Oil', 5, NULL), (2, 'Sauce', -2, 1)")
        )
        connection.execute(sa.text("INSERT INTO product (id, restaurant_id) VALUES (1, 1), (2, 2)"))
        migration = load_migration()
        with pytest.raises(ValueError):
            run_migration(connection, migration.upgrade)


def test_sqlite_foreign_keys_are_enabled_for_inventory_migration_checks():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("restaurant", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "inventory_item",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("restaurant_id", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurant.id"]),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(sa.text("PRAGMA foreign_keys = ON"))
        connection.execute(sa.text("INSERT INTO restaurant (id) VALUES (1)"))
        connection.execute(sa.text("INSERT INTO inventory_item (id, restaurant_id, quantity) VALUES (1, 1, 10)"))
        with pytest.raises(Exception):
            connection.execute(sa.text("INSERT INTO inventory_item (id, restaurant_id, quantity) VALUES (2, 99, 9)"))