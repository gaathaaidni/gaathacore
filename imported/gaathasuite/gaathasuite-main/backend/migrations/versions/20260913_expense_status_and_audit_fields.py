"""Add status and audit columns to expenses.

Revision ID: 20260913_expense_status_audit
Revises: 20260912_invoice_line_org_scope
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260913_expense_status_audit"
down_revision = "20260912_invoice_line_org_scope"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [column["name"] for column in insp.get_columns("expenses")]
    approval_cols = [column["name"] for column in insp.get_columns("approval_requests")]

    if "status" not in cols:
        op.add_column("expenses", sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"))
    if "created_by" not in cols:
        op.add_column("expenses", sa.Column("created_by", sa.Integer(), nullable=True))
    if "updated_at" not in cols:
        op.add_column(
            "expenses",
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    op.execute("UPDATE expenses SET status = 'pending' WHERE status IS NULL")
    op.alter_column("expenses", "status", server_default=None)

    if "amount" not in approval_cols:
        op.add_column(
            "approval_requests",
            sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [column["name"] for column in insp.get_columns("expenses")]

    if "updated_at" in cols:
        op.drop_column("expenses", "updated_at")
    if "created_by" in cols:
        op.drop_column("expenses", "created_by")
    if "status" in cols:
        op.drop_column("expenses", "status")

    approval_cols = [column["name"] for column in insp.get_columns("approval_requests")]
    if "amount" in approval_cols:
        op.drop_column("approval_requests", "amount")
