"""Create the canonical application schema on a fresh installation."""

from alembic import op
import sqlalchemy as sa

from app import models  # noqa: F401
from app.db import Base


revision = "20260909_fresh_schema_bootstrap"
down_revision = "phase21_merge_20260910"
branch_labels = None
depends_on = None


LEGACY_MODERN_TABLES = ("department", "invoice", "invoice_line", "invoice_sequence")
DEFERRED_TABLES = {
    "fulfillments",
    "legal_acceptances",
    "legal_documents",
    "notification_preferences",
    "purchase_receipt_lines",
    "purchase_receipts",
    "quotation_lines",
    "quotations",
    "sales_order_lines",
    "sales_orders",
    "settings_change_log",
    "vendor_bill_payments",
    "vendor_bills",
}
DEFERRED_COLUMNS = {
    "approval_requests": {"amount", "rejection_reason"},
    "expenses": {"created_by", "status", "updated_at"},
    "invoice": {"paid_amount"},
    "invoice_line": {"organization_id"},
    "payment": {"organization_id"},
}


def _inspector():
    return sa.inspect(op.get_bind())


def _create_missing_tables():
    inspector = _inspector()
    existing = set(inspector.get_table_names())

    for source_table in Base.metadata.sorted_tables:
        if source_table.name in existing or source_table.name in DEFERRED_TABLES:
            continue

        metadata = sa.MetaData()
        table = source_table.to_metadata(metadata)
        deferred_columns = DEFERRED_COLUMNS.get(table.name, set())
        columns = [
            column.copy()
            for column in table.columns
            if column.name not in deferred_columns
        ]
        if table.name == "payment":
            for column in columns:
                if column.name == "amount":
                    column.type = sa.Float()
        constraints = [
            constraint.copy()
            for constraint in list(table.constraints)
            if not deferred_columns.intersection(
                column.name for column in constraint.columns
            )
        ]
        op.create_table(
            table.name,
            *columns,
            *constraints,
        )
        existing.add(table.name)

    if "notification_preferences" not in existing:
        op.create_table(
            "notification_preferences",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("email_enabled", sa.Boolean(), nullable=True),
            sa.Column("in_app_enabled", sa.Boolean(), nullable=True),
            sa.Column("digest_enabled", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("user_id"),
        )


def _complete_historical_modern_tables():
    inspector = _inspector()
    metadata_tables = {table.name: table for table in Base.metadata.sorted_tables}

    for table_name in LEGACY_MODERN_TABLES:
        source_table = metadata_tables[table_name]
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        deferred_columns = DEFERRED_COLUMNS.get(table_name, set())
        for source_column in source_table.columns:
            if source_column.name in existing_columns or source_column.name in deferred_columns:
                continue
            column = source_column.copy()
            column.nullable = True
            column.server_default = None
            op.add_column(table_name, column)


def upgrade():
    _create_missing_tables()
    _complete_historical_modern_tables()


def downgrade():
    raise RuntimeError("Downgrade disabled for fresh-schema bootstrap; use a reviewed forward migration.")
