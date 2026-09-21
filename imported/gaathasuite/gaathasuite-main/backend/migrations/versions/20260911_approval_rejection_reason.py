"""Store approval rejection reasons.

Revision ID: 20260911_appr_rej_reason
Revises: 20260910_hr_tenant_not_null
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260911_appr_rej_reason"
down_revision = "20260910_hr_tenant_not_null"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "approval_requests",
        sa.Column("rejection_reason", sa.String(length=2000), nullable=True),
    )


def downgrade():
    op.drop_column("approval_requests", "rejection_reason")
