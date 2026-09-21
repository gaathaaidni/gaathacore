"""Add journal entry lifecycle status for posted-entry immutability."""

from alembic import op
import sqlalchemy as sa

revision = "20260922_journal_immutability"
down_revision = "20260921_vendor_bill_payments"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("journal_entry")}
    if "status" not in columns:
        op.add_column(
            "journal_entry",
            sa.Column("status", sa.String(length=20), nullable=True, server_default="posted"),
        )
        op.execute("UPDATE journal_entry SET status = 'posted' WHERE status IS NULL")
        op.alter_column("journal_entry", "status", nullable=False, server_default="draft")


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("journal_entry")}
    if "status" in columns:
        op.drop_column("journal_entry", "status")
