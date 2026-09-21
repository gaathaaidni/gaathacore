"""Create settings change log table.

Revision ID: 20260914_settings_change_log
Revises: 20260913_expense_status_audit
Create Date: 2026-09-14
"""

from alembic import op
import sqlalchemy as sa

revision = "20260914_settings_change_log"
down_revision = "20260913_expense_status_audit"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("settings_change_log"):
        op.create_table(
            "settings_change_log",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("changed_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.Column("changes", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        )
        op.create_index("ix_settings_change_log_id", "settings_change_log", ["id"], unique=False)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("settings_change_log")}
    if "created_at" not in existing_columns:
        op.add_column("settings_change_log", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    if "updated_at" not in existing_columns:
        op.add_column("settings_change_log", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    if "is_active" not in existing_columns:
        op.add_column("settings_change_log", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))


def downgrade():
    bind = op.get_bind()
    if sa.inspect(bind).has_table("settings_change_log"):
        op.drop_index("ix_settings_change_log_id", table_name="settings_change_log")
        op.drop_table("settings_change_log")
