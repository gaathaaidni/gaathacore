"""Add organization scope to invoice_line table.

Revision ID: 20260912_invoice_line_org_scope
Revises: 20260911_legal_base_fields
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa

revision = "20260912_invoice_line_org_scope"
down_revision = "20260911_legal_base_fields"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [column["name"] for column in insp.get_columns("invoice_line")]
    if "organization_id" not in cols:
        op.add_column(
            "invoice_line",
            sa.Column("organization_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            op.f("ix_invoice_line_organization_id"),
            "invoice_line",
            ["organization_id"],
            unique=False,
        )

    # Backfill existing rows to the owning invoice's org when possible.
    op.execute(
        "UPDATE invoice_line il SET organization_id = inv.organization_id "
        "FROM invoice inv WHERE il.invoice_id = inv.id AND il.organization_id IS NULL"
    )

    op.alter_column("invoice_line", "organization_id", nullable=False)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [column["name"] for column in insp.get_columns("invoice_line")]
    if "organization_id" in cols:
        op.drop_index(op.f("ix_invoice_line_organization_id"), table_name="invoice_line")
        op.drop_column("invoice_line", "organization_id")
