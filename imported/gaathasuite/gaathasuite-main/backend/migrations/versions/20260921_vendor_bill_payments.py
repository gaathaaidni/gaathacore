"""Add vendor bill payment records.

Revision ID: 20260921_vendor_bill_payments
Revises: 20260920_decimal_payments
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa

revision = "20260921_vendor_bill_payments"
down_revision = "20260920_decimal_payments"
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("vendor_bill_payments"):
        op.create_table(
            "vendor_bill_payments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("organization_id", sa.Integer(), nullable=False),
            sa.Column("vendor_bill_id", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("payment_date", sa.Date(), nullable=False),
            sa.Column("reference", sa.String(255), nullable=False),
            sa.ForeignKeyConstraint(["vendor_bill_id"], ["vendor_bills.id"]),
        )
        op.create_index("ix_vendor_bill_payments_organization_id", "vendor_bill_payments", ["organization_id"])
        op.create_index("ix_vendor_bill_payments_vendor_bill_id", "vendor_bill_payments", ["vendor_bill_id"])


def downgrade():
    op.drop_index("ix_vendor_bill_payments_vendor_bill_id", table_name="vendor_bill_payments")
    op.drop_index("ix_vendor_bill_payments_organization_id", table_name="vendor_bill_payments")
    op.drop_table("vendor_bill_payments")
