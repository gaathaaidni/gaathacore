"""Use numeric money fields and scope customer payments.

Revision ID: 20260920_decimal_payments
Revises: 20260919_transaction_parity
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa

revision = "20260920_decimal_payments"
down_revision = "20260919_transaction_parity"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("invoice", "total_amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), postgresql_using="total_amount::numeric")
    op.alter_column("invoice", "paid_amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), postgresql_using="paid_amount::numeric")
    op.alter_column("payment", "amount", existing_type=sa.Float(), type_=sa.Numeric(12, 2), postgresql_using="amount::numeric")
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("payment")}
    if "organization_id" not in columns:
        op.add_column("payment", sa.Column("organization_id", sa.Integer(), nullable=True))
        op.execute("UPDATE payment p SET organization_id = i.organization_id FROM invoice i WHERE p.invoice_id = i.id")
        op.alter_column("payment", "organization_id", nullable=False)
        op.create_index("ix_payment_organization_id", "payment", ["organization_id"])


def downgrade():
    op.drop_index("ix_payment_organization_id", table_name="payment")
    op.drop_column("payment", "organization_id")
    op.alter_column("payment", "amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), postgresql_using="amount::double precision")
    op.alter_column("invoice", "paid_amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), postgresql_using="paid_amount::double precision")
    op.alter_column("invoice", "total_amount", existing_type=sa.Numeric(12, 2), type_=sa.Float(), postgresql_using="total_amount::double precision")
