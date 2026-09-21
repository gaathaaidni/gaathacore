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
    with op.batch_alter_table("payment_transaction") as batch_op:
        batch_op.add_column(sa.Column("cash_register_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cashier_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("restaurant_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_payment_transaction_cash_register", "cash_register", ["cash_register_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_payment_transaction_cashier", "cashier_account", ["cashier_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_payment_transaction_restaurant", "restaurant", ["restaurant_id"], ["id"]
        )
    op.execute(sa.text(
        'UPDATE payment_transaction SET restaurant_id = '
        '(SELECT restaurant_id FROM "order" WHERE "order".id = payment_transaction.order_id)'
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

    op.create_index(
        "uq_payment_transaction_restaurant_reference",
        "payment_transaction",
        ["restaurant_id", "reference_id"],
        unique=True,
        sqlite_where=sa.text("reference_id IS NOT NULL AND reference_id <> ''"),
        postgresql_where=sa.text("reference_id IS NOT NULL AND reference_id <> ''"),
    )


def downgrade():
    op.drop_index("uq_payment_transaction_restaurant_reference", table_name="payment_transaction")
    with op.batch_alter_table("payment_transaction") as batch_op:
        batch_op.drop_constraint("fk_payment_transaction_restaurant", type_="foreignkey")
        batch_op.drop_constraint("fk_payment_transaction_cashier", type_="foreignkey")
        batch_op.drop_constraint("fk_payment_transaction_cash_register", type_="foreignkey")
        batch_op.drop_column("restaurant_id")
        batch_op.drop_column("cashier_id")
        batch_op.drop_column("cash_register_id")