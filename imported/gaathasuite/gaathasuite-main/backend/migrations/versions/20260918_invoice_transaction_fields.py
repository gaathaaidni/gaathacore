"""Add invoice transaction fields.

Revision ID: 20260918_invoice_transaction
Revises: 20260917_erp_transactions
Create Date: 2026-09-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260918_invoice_transaction"
down_revision = "20260917_erp_transactions"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table, column, definition in (
        ("invoice", "paid_amount", sa.Column("paid_amount", sa.Float(), nullable=False, server_default="0")),
        ("invoice_line", "item_id", sa.Column("item_id", sa.Integer(), nullable=True)),
    ):
        columns = {item["name"] for item in sa.inspect(bind).get_columns(table)}
        if column not in columns:
            op.add_column(table, definition)
    if not any(fk["constrained_columns"] == ["item_id"] for fk in sa.inspect(bind).get_foreign_keys("invoice_line")):
        op.create_foreign_key("fk_invoice_line_item", "invoice_line", "items", ["item_id"], ["id"])
    op.alter_column("invoice", "paid_amount", server_default=None)


def downgrade():
    op.drop_constraint("fk_invoice_line_item", "invoice_line", type_="foreignkey")
    op.drop_column("invoice_line", "item_id")
    op.drop_column("invoice", "paid_amount")
