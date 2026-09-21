"""Align legal tables with shared model base fields.

Revision ID: 20260911_legal_base_fields
Revises: 20260911_legal_consent
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa

revision = "20260911_legal_base_fields"
down_revision = "20260911_legal_consent"
branch_labels = None
depends_on = None


def upgrade():
    for table_name in ("legal_documents", "legal_acceptances"):
        op.add_column(
            table_name,
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.add_column(
            table_name,
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    op.add_column(
        "legal_acceptances",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_column("legal_acceptances", "created_at")
    for table_name in ("legal_acceptances", "legal_documents"):
        op.drop_column(table_name, "is_active")
        op.drop_column(table_name, "updated_at")
