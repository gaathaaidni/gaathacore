import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext


MIGRATION_PATH = Path(__file__).parents[1] / "migrations" / "versions" / "008_add_payment_register_context.py"


def load_migration():
    spec = importlib.util.spec_from_file_location("migration_008", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def make_database():
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table("restaurant", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("cash_register", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("cashier_account", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table(
        "order",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("restaurant_id", sa.Integer, nullable=False),
    )
    sa.Table(
        "payment_transaction",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, nullable=False),
        sa.Column("reference_id", sa.String(128), nullable=True),
    )
    metadata.create_all(engine)
    return engine


def run_migration(connection, operation):
    context = MigrationContext.configure(connection)
    with Operations.context(context):
        operation()


def seed_database(connection, duplicate=False):
    connection.execute(sa.text("INSERT INTO restaurant (id) VALUES (1), (2)"))
    connection.execute(sa.text("INSERT INTO cash_register (id) VALUES (1)"))
    connection.execute(sa.text("INSERT INTO cashier_account (id) VALUES (1)"))
    connection.execute(
        sa.text("INSERT INTO \"order\" (id, restaurant_id) VALUES (1, 1), (2, 2)")
    )
    rows = [(1, 1, "gateway-1"), (2, 2, "gateway-1"), (3, 1, None), (4, 1, "")]
    if duplicate:
        rows.append((5, 1, "gateway-1"))
    connection.execute(
        sa.text(
            "INSERT INTO payment_transaction (id, order_id, reference_id) "
            "VALUES (:id, :order_id, :reference_id)"
        ),
        [
            {"id": row_id, "order_id": order_id, "reference_id": reference_id}
            for row_id, order_id, reference_id in rows
        ],
    )


def test_fresh_upgrade_and_downgrade():
    engine = make_database()
    with engine.begin() as connection:
        seed_database(connection)
        migration = load_migration()
        run_migration(connection, migration.upgrade)

        assert connection.execute(sa.text("SELECT COUNT(*) FROM payment_transaction")).scalar_one() == 4
        assert connection.execute(
            sa.text("SELECT restaurant_id FROM payment_transaction WHERE id = 1")
        ).scalar_one() == 1

        run_migration(connection, migration.downgrade)
        columns = sa.inspect(connection).get_columns("payment_transaction")
        assert {column["name"] for column in columns} == {"id", "order_id", "reference_id"}


def test_duplicate_historical_references_are_preserved_and_new_duplicates_rejected():
    engine = make_database()
    with engine.begin() as connection:
        seed_database(connection, duplicate=True)
        migration = load_migration()
        run_migration(connection, migration.upgrade)

        rows = connection.execute(
            sa.text(
                "SELECT id, restaurant_id, reference_id FROM payment_transaction "
                "ORDER BY id"
            )
        ).mappings().all()
        assert len(rows) == 5
        assert [row["id"] for row in rows] == [1, 2, 3, 4, 5]
        assert rows[0]["reference_id"] == "gateway-1"
        assert rows[4]["reference_id"].startswith("gateway-1-historical-duplicate-5")
        assert rows[2]["reference_id"] is None
        assert rows[3]["reference_id"] == ""

        with pytest.raises(sa.exc.IntegrityError):
            connection.execute(
                sa.text(
                    "INSERT INTO payment_transaction "
                    "(id, order_id, restaurant_id, reference_id) "
                    "VALUES (6, 1, 1, 'gateway-1')"
                )
            )

        connection.execute(
            sa.text(
                "INSERT INTO payment_transaction "
                    "(id, order_id, restaurant_id, reference_id) "
                    "VALUES (7, 1, 1, 'new-reference')"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO payment_transaction "
                    "(id, order_id, restaurant_id, reference_id) "
                    "VALUES (8, 2, 2, 'tenant-scoped-reference')"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO payment_transaction "
                    "(id, order_id, restaurant_id, reference_id) "
                    "VALUES (9, 1, 1, 'tenant-scoped-reference')"
            )
        )
        connection.execute(
            sa.text(
                "INSERT INTO payment_transaction "
                    "(id, order_id, restaurant_id, reference_id) "
                    "VALUES (10, 1, 1, NULL), (11, 1, 1, '')"
            )
        )
        assert connection.execute(sa.text("SELECT COUNT(*) FROM payment_transaction")).scalar_one() == 10
