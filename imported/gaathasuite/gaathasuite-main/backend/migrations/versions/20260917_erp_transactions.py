"""Create minimum integrated sales and purchasing transaction tables.

Revision ID: 20260917_erp_transactions
Revises: 20260916_legal_tz
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260917_erp_transactions"
down_revision = "20260916_legal_tz"
branch_labels = None
depends_on = None


def common_columns():
    return [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    ]


def upgrade():
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "quotations" not in tables:
        op.create_table("quotations", *common_columns(),
            sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("quotation_number", sa.String(50), nullable=False), sa.Column("status", sa.String(30), nullable=False),
            sa.Column("quotation_date", sa.Date(), nullable=False), sa.Column("valid_until", sa.Date()), sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("subtotal", sa.Numeric(12, 2), nullable=False), sa.Column("tax", sa.Numeric(12, 2), nullable=False), sa.Column("total", sa.Numeric(12, 2), nullable=False),
            sa.Column("notes", sa.Text()), sa.Column("created_by", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]), sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )
        op.create_index("ix_quotations_organization_id", "quotations", ["organization_id"])
        op.create_index("ix_quotations_quotation_number", "quotations", ["quotation_number"], unique=True)
    if "quotation_lines" not in tables:
        op.create_table("quotation_lines", *common_columns(), sa.Column("quotation_id", sa.Integer(), nullable=False), sa.Column("item_id", sa.Integer(), nullable=False), sa.Column("description", sa.String(300), nullable=False), sa.Column("quantity", sa.Numeric(12, 3), nullable=False), sa.Column("unit_price", sa.Numeric(12, 2), nullable=False), sa.Column("tax", sa.Numeric(12, 2), nullable=False), sa.Column("line_total", sa.Numeric(12, 2), nullable=False), sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"]), sa.ForeignKeyConstraint(["item_id"], ["items.id"]),)
    if "sales_orders" not in tables:
        op.create_table("sales_orders", *common_columns(), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("customer_id", sa.Integer(), nullable=False), sa.Column("quotation_id", sa.Integer()), sa.Column("order_number", sa.String(50), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("order_date", sa.Date(), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("subtotal", sa.Numeric(12, 2), nullable=False), sa.Column("tax", sa.Numeric(12, 2), nullable=False), sa.Column("total", sa.Numeric(12, 2), nullable=False), sa.Column("notes", sa.Text()), sa.Column("created_by", sa.Integer(), nullable=False), sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]), sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"]), sa.ForeignKeyConstraint(["created_by"], ["users.id"]),)
        op.create_index("ix_sales_orders_organization_id", "sales_orders", ["organization_id"])
        op.create_index("ix_sales_orders_order_number", "sales_orders", ["order_number"], unique=True)
    if "sales_order_lines" not in tables:
        op.create_table("sales_order_lines", *common_columns(), sa.Column("sales_order_id", sa.Integer(), nullable=False), sa.Column("item_id", sa.Integer(), nullable=False), sa.Column("description", sa.String(300), nullable=False), sa.Column("quantity", sa.Numeric(12, 3), nullable=False), sa.Column("unit_price", sa.Numeric(12, 2), nullable=False), sa.Column("tax", sa.Numeric(12, 2), nullable=False), sa.Column("line_total", sa.Numeric(12, 2), nullable=False), sa.Column("fulfilled_quantity", sa.Numeric(12, 3), nullable=False), sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"]), sa.ForeignKeyConstraint(["item_id"], ["items.id"]),)
    if "fulfillments" not in tables:
        op.create_table("fulfillments", *common_columns(), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("sales_order_id", sa.Integer(), nullable=False), sa.Column("warehouse_id", sa.Integer(), nullable=False), sa.Column("fulfillment_number", sa.String(50), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("fulfilled_at", sa.DateTime(), server_default=sa.text("now()")), sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"]), sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse.id"]),)
    if "purchase_receipts" not in tables:
        op.create_table("purchase_receipts", *common_columns(), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("purchase_order_id", sa.Integer(), nullable=False), sa.Column("vendor_id", sa.Integer(), nullable=False), sa.Column("warehouse_id", sa.Integer(), nullable=False), sa.Column("receipt_number", sa.String(50), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("received_at", sa.DateTime(), server_default=sa.text("now()")), sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]), sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]), sa.ForeignKeyConstraint(["warehouse_id"], ["warehouse.id"]),)
    if "purchase_receipt_lines" not in tables:
        op.create_table("purchase_receipt_lines", *common_columns(), sa.Column("receipt_id", sa.Integer(), nullable=False), sa.Column("item_id", sa.Integer(), nullable=False), sa.Column("ordered_quantity", sa.Numeric(12, 3), nullable=False), sa.Column("received_quantity", sa.Numeric(12, 3), nullable=False), sa.ForeignKeyConstraint(["receipt_id"], ["purchase_receipts.id"]), sa.ForeignKeyConstraint(["item_id"], ["items.id"]),)
    if "vendor_bills" not in tables:
        op.create_table("vendor_bills", *common_columns(), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("vendor_id", sa.Integer(), nullable=False), sa.Column("purchase_order_id", sa.Integer()), sa.Column("bill_number", sa.String(50), nullable=False), sa.Column("bill_date", sa.Date(), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("subtotal", sa.Numeric(12, 2), nullable=False), sa.Column("tax", sa.Numeric(12, 2), nullable=False), sa.Column("total", sa.Numeric(12, 2), nullable=False), sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]), sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),)
        op.create_index("ix_vendor_bills_organization_id", "vendor_bills", ["organization_id"])
        op.create_index("ix_vendor_bills_bill_number", "vendor_bills", ["bill_number"], unique=True)


def downgrade():
    for table in ("vendor_bills", "purchase_receipt_lines", "purchase_receipts", "fulfillments", "sales_order_lines", "sales_orders", "quotation_lines", "quotations"):
        op.drop_table(table)
