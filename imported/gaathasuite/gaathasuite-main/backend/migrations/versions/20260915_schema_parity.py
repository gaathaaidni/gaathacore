"""Resolve remaining additive model/schema parity differences.

Revision ID: 20260915_schema_parity
Revises: 20260914_settings_change_log
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa

revision = "20260915_schema_parity"
down_revision = "20260914_settings_change_log"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    settings_columns = {column["name"] for column in inspector.get_columns("settings_change_log")}
    if "created_at" not in settings_columns:
        op.add_column("settings_change_log", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    if "updated_at" not in settings_columns:
        op.add_column("settings_change_log", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    if "is_active" not in settings_columns:
        op.add_column("settings_change_log", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))

    legal_columns = {column["name"]: column for column in inspector.get_columns("legal_documents")}
    if legal_columns.get("created_at", {}).get("nullable", True):
        op.execute("UPDATE legal_documents SET created_at = now() WHERE created_at IS NULL")
        op.alter_column("legal_documents", "created_at", nullable=False)

    constraints = inspector.get_unique_constraints("legal_documents")
    for constraint in constraints:
        if constraint.get("name") == "uq_legal_documents_slug":
            op.drop_constraint("uq_legal_documents_slug", "legal_documents", type_="unique")

    indexes = inspector.get_indexes("legal_documents")
    for index in indexes:
        if index.get("name") == "ix_legal_documents_slug":
            op.drop_index("ix_legal_documents_slug", table_name="legal_documents")

    if not any(index.get("name") == "ix_legal_documents_slug" and index.get("unique") for index in indexes):
        op.create_index("ix_legal_documents_slug", "legal_documents", ["slug"], unique=True)


def downgrade():
    op.drop_index("ix_legal_documents_slug", table_name="legal_documents")
    op.create_index("ix_legal_documents_slug", "legal_documents", ["slug"], unique=False)
    op.create_unique_constraint("uq_legal_documents_slug", "legal_documents", ["slug"])
    op.alter_column("legal_documents", "created_at", nullable=True)
    for column in ("is_active", "updated_at", "created_at"):
        op.drop_column("settings_change_log", column)
