"""Align legal document created_at with shared timezone-aware timestamps.

Revision ID: 20260916_legal_tz
Revises: 20260915_schema_parity
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa

revision = "20260916_legal_tz"
down_revision = "20260915_schema_parity"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "legal_documents",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )


def downgrade():
    op.alter_column(
        "legal_documents",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
