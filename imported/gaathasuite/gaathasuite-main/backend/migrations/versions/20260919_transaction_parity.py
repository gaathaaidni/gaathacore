"""Align transaction indexes and timestamp nullability.

Revision ID: 20260919_transaction_parity
Revises: 20260918_invoice_transaction
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_transaction_parity"
down_revision = "20260918_invoice_transaction"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    indexes = {
        index["name"] for table in (
            "fulfillments", "purchase_receipt_lines", "purchase_receipts",
            "quotation_lines", "quotations", "sales_order_lines", "sales_orders", "vendor_bills",
        ) for index in sa.inspect(bind).get_indexes(table)
    }
    wanted = (
        ("ix_fulfillments_fulfillment_number", "fulfillments", "fulfillment_number", True),
        ("ix_fulfillments_organization_id", "fulfillments", "organization_id", False),
        ("ix_fulfillments_sales_order_id", "fulfillments", "sales_order_id", False),
        ("ix_purchase_receipt_lines_receipt_id", "purchase_receipt_lines", "receipt_id", False),
        ("ix_purchase_receipts_organization_id", "purchase_receipts", "organization_id", False),
        ("ix_purchase_receipts_purchase_order_id", "purchase_receipts", "purchase_order_id", False),
        ("ix_purchase_receipts_receipt_number", "purchase_receipts", "receipt_number", True),
        ("ix_purchase_receipts_vendor_id", "purchase_receipts", "vendor_id", False),
        ("ix_quotation_lines_quotation_id", "quotation_lines", "quotation_id", False),
        ("ix_quotations_customer_id", "quotations", "customer_id", False),
        ("ix_sales_order_lines_sales_order_id", "sales_order_lines", "sales_order_id", False),
        ("ix_sales_orders_customer_id", "sales_orders", "customer_id", False),
        ("ix_vendor_bills_vendor_id", "vendor_bills", "vendor_id", False),
    )
    for name, table, column, unique in wanted:
        if name not in indexes:
            op.create_index(name, table, [column], unique=unique)

    for table, column in (("fulfillments", "fulfilled_at"), ("purchase_receipts", "received_at")):
        op.execute(f"UPDATE {table} SET {column} = now() WHERE {column} IS NULL")
        op.alter_column(table, column, nullable=False)


def downgrade():
    for name, table, _column, _unique in (
        ("ix_fulfillments_fulfillment_number", "fulfillments", "fulfillment_number", True),
        ("ix_fulfillments_organization_id", "fulfillments", "organization_id", False),
        ("ix_fulfillments_sales_order_id", "fulfillments", "sales_order_id", False),
        ("ix_purchase_receipt_lines_receipt_id", "purchase_receipt_lines", "receipt_id", False),
        ("ix_purchase_receipts_organization_id", "purchase_receipts", "organization_id", False),
        ("ix_purchase_receipts_purchase_order_id", "purchase_receipts", "purchase_order_id", False),
        ("ix_purchase_receipts_receipt_number", "purchase_receipts", "receipt_number", True),
        ("ix_purchase_receipts_vendor_id", "purchase_receipts", "vendor_id", False),
        ("ix_quotation_lines_quotation_id", "quotation_lines", "quotation_id", False),
        ("ix_quotations_customer_id", "quotations", "customer_id", False),
        ("ix_sales_order_lines_sales_order_id", "sales_order_lines", "sales_order_id", False),
        ("ix_sales_orders_customer_id", "sales_orders", "customer_id", False),
        ("ix_vendor_bills_vendor_id", "vendor_bills", "vendor_id", False),
    ):
        op.drop_index(name, table_name=table)
