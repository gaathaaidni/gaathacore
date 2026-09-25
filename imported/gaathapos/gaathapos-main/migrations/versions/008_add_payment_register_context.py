"""Add register context to payment transactions.

Revision ID: 008_add_payment_register_context
Revises: 14e61ca71ed7
"""
from alembic import op
import sqlalchemy as sa


revision = "008_add_payment_register_context"
down_revision = "14e61ca71ed7"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {col['name'] for col in inspector.get_columns('payment_transaction')}
    fks = {fk.get('name') for fk in inspector.get_foreign_keys('payment_transaction')}

    with op.batch_alter_table("payment_transaction") as batch_op:
        if "cash_register_id" not in cols:
            batch_op.add_column(sa.Column("cash_register_id", sa.Integer(), nullable=True))
        if "cashier_id" not in cols:
            batch_op.add_column(sa.Column("cashier_id", sa.Integer(), nullable=True))
        if "restaurant_id" not in cols:
            batch_op.add_column(sa.Column("restaurant_id", sa.Integer(), nullable=True))

        if "fk_payment_transaction_cash_register" not in fks:
            batch_op.create_foreign_key(
                "fk_payment_transaction_cash_register", "cash_register", ["cash_register_id"], ["id"]
            )
        if "fk_payment_transaction_cashier" not in fks:
            batch_op.create_foreign_key(
                "fk_payment_transaction_cashier", "cashier_account", ["cashier_id"], ["id"]
            )
        if "fk_payment_transaction_restaurant" not in fks:
            batch_op.create_foreign_key(
                "fk_payment_transaction_restaurant", "restaurant", ["restaurant_id"], ["id"]
            )

    op.execute(sa.text(
        'UPDATE payment_transaction SET restaurant_id = '
        '(SELECT restaurant_id FROM "order" WHERE "order".id = payment_transaction.order_id) '
        'WHERE restaurant_id IS NULL'
    ))

    connection = op.get_bind()
    payment_rows = list(connection.execute(sa.text(
        "SELECT id, restaurant_id, reference_id "
        "FROM payment_transaction "
        "WHERE reference_id IS NOT NULL AND reference_id <> '' "
        "ORDER BY restaurant_id, reference_id, id"
    )).mappings())
    seen_references = set()
    used_references = {
        (payment["restaurant_id"], payment["reference_id"])
        for payment in payment_rows
    }
    for payment in payment_rows:
        key = (payment["restaurant_id"], payment["reference_id"])
        if key not in seen_references:
            seen_references.add(key)
            continue

        duplicate_number = 1
        suffix = f"-historical-duplicate-{payment['id']}"
        reference_id = payment["reference_id"]
        normalized_reference = f"{reference_id[:128 - len(suffix)]}{suffix}"
        while (payment["restaurant_id"], normalized_reference) in used_references:
            duplicate_number += 1
            suffix = f"-historical-duplicate-{payment['id']}-{duplicate_number}"
            normalized_reference = f"{reference_id[:128 - len(suffix)]}{suffix}"

        connection.execute(
            sa.text(
                "UPDATE payment_transaction SET reference_id = :reference_id "
                "WHERE id = :payment_id"
            ),
            {"reference_id": normalized_reference, "payment_id": payment["id"]},
        )
        seen_references.add((payment["restaurant_id"], normalized_reference))
        used_references.add((payment["restaurant_id"], normalized_reference))

    indexes = {ix['name'] for ix in inspector.get_indexes('payment_transaction')}
    if "uq_payment_transaction_restaurant_reference" not in indexes:
        op.create_index(
            "uq_payment_transaction_restaurant_reference",
            "payment_transaction",
            ["restaurant_id", "reference_id"],
            unique=True,
            sqlite_where=sa.text("reference_id IS NOT NULL AND reference_id <> ''"),
            postgresql_where=sa.text("reference_id IS NOT NULL AND reference_id <> ''"),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {ix['name'] for ix in inspector.get_indexes('payment_transaction')}
    if "uq_payment_transaction_restaurant_reference" in indexes:
        op.drop_index("uq_payment_transaction_restaurant_reference", table_name="payment_transaction")

    cols = {col['name'] for col in inspector.get_columns('payment_transaction')}
    fks = {fk.get('name') for fk in inspector.get_foreign_keys('payment_transaction')}

    with op.batch_alter_table("payment_transaction") as batch_op:
        if "fk_payment_transaction_restaurant" in fks:
            batch_op.drop_constraint("fk_payment_transaction_restaurant", type_="foreignkey")
        if "fk_payment_transaction_cashier" in fks:
            batch_op.drop_constraint("fk_payment_transaction_cashier", type_="foreignkey")
        if "fk_payment_transaction_cash_register" in fks:
            batch_op.drop_constraint("fk_payment_transaction_cash_register", type_="foreignkey")
        if "restaurant_id" in cols:
            batch_op.drop_column("restaurant_id")
        if "cashier_id" in cols:
            batch_op.drop_column("cashier_id")
        if "cash_register_id" in cols:
            batch_op.drop_column("cash_register_id")
