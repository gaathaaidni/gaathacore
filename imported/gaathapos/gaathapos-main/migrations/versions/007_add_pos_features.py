"""Add comprehensive POS features

Revision ID: 007_add_pos_features
Revises: 006_add_restaurant_store_settings
Create Date: 2025-12-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_pos_features'
down_revision = '006_add_restaurant_store_settings'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create ProductCategory table
    if 'product_category' not in existing_tables:
        op.create_table(
            'product_category',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('display_order', sa.Integer(), default=0),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.ForeignKeyConstraint(['parent_id'], ['product_category.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create Product table
    if 'product' not in existing_tables:
        op.create_table(
            'product',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('sku', sa.String(64), nullable=True),
            sa.Column('base_price', sa.Float(), nullable=False),
            sa.Column('cost', sa.Float(), nullable=True),
            sa.Column('available', sa.Boolean(), default=True),
            sa.Column('requires_weight', sa.Boolean(), default=False),
            sa.Column('unit_of_measure', sa.String(32), default='unit'),
            sa.Column('weight', sa.Float(), nullable=True),
            sa.Column('ship_later', sa.Boolean(), default=False),
            sa.Column('is_gift_card', sa.Boolean(), default=False),
            sa.Column('gift_card_validity_days', sa.Integer(), nullable=True),
            sa.Column('image_url', sa.String(255), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.ForeignKeyConstraint(['category_id'], ['product_category.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create ProductVariant table
    if 'product_variant' not in existing_tables:
        op.create_table(
            'product_variant',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('sku', sa.String(64), nullable=True),
            sa.Column('price_adjustment', sa.Float(), default=0.0),
            sa.Column('cost_adjustment', sa.Float(), default=0.0),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create BarcodeMapping table
    if 'barcode_mapping' not in existing_tables:
        op.create_table(
            'barcode_mapping',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('barcode', sa.String(128), nullable=False),
            sa.Column('variant_id', sa.Integer(), nullable=True),
            sa.Column('embedded_price', sa.Float(), nullable=True),
            sa.Column('embedded_weight', sa.Float(), nullable=True),
            sa.Column('loyalty_points', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.ForeignKeyConstraint(['variant_id'], ['product_variant.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('barcode', name='uix_barcode')
        )

    # Create PaymentMethod table
    if 'payment_method' not in existing_tables:
        op.create_table(
            'payment_method',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('payment_type', sa.String(20), nullable=False),
            sa.Column('requires_external_terminal', sa.Boolean(), default=False),
            sa.Column('can_be_reused', sa.Boolean(), default=True),
            sa.Column('currency_rounding', sa.Float(), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create PaymentTransaction table
    if 'payment_transaction' not in existing_tables:
        op.create_table(
            'payment_transaction',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('payment_method_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(3), nullable=False),
            sa.Column('status', sa.String(20), default='pending'),
            sa.Column('reference_id', sa.String(128), nullable=True),
            sa.Column('is_offline', sa.Boolean(), default=False),
            sa.Column('synchronization_status', sa.String(20), default='synced'),
            sa.Column('tip_amount', sa.Float(), default=0.0),
            sa.Column('tip_type', sa.String(20), nullable=True),
            sa.Column('change_to_tip', sa.Boolean(), default=False),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.ForeignKeyConstraint(['payment_method_id'], ['payment_method.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create Discount table
    if 'discount' not in existing_tables:
        op.create_table(
            'discount',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('discount_type', sa.String(20), nullable=False),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('applies_to', sa.String(20), default='product'),
            sa.Column('product_id', sa.Integer(), nullable=True),
            sa.Column('customer_id', sa.Integer(), nullable=True),
            sa.Column('start_date', sa.DateTime(), nullable=True),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('min_quantity', sa.Integer(), default=1),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create BillSplit table
    if 'bill_split' not in existing_tables:
        op.create_table(
            'bill_split',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('split_index', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('payment_method_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(20), default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.ForeignKeyConstraint(['payment_method_id'], ['payment_method.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create Receipt table
    if 'receipt' not in existing_tables:
        op.create_table(
            'receipt',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('receipt_number', sa.String(64), nullable=True),
            sa.Column('header_text', sa.Text(), nullable=True),
            sa.Column('footer_text', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('printed', sa.Boolean(), default=False),
            sa.Column('printed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('receipt_number', name='uix_receipt_number')
        )

    # Create RestaurantFloorPlan table
    if 'restaurant_floor_plan' not in existing_tables:
        op.create_table(
            'restaurant_floor_plan',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), default='Main Floor'),
            sa.Column('layout_data', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('restaurant_id', name='uix_restaurant_floor_plan')
        )

    # Create TableSection table
    if 'table_section' not in existing_tables:
        op.create_table(
            'table_section',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('floor_plan_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('capacity', sa.Integer(), default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['floor_plan_id'], ['restaurant_floor_plan.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create Table table
    if 'table' not in existing_tables:
        op.create_table(
            'table',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('section_id', sa.Integer(), nullable=False),
            sa.Column('table_number', sa.String(32), nullable=False),
            sa.Column('seats', sa.Integer(), default=2),
            sa.Column('pos_x', sa.Float(), nullable=True),
            sa.Column('pos_y', sa.Float(), nullable=True),
            sa.Column('status', sa.String(20), default='available'),
            sa.Column('current_order_id', sa.Integer(), nullable=True),
            sa.Column('reserved_by', sa.String(128), nullable=True),
            sa.Column('reserved_until', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['section_id'], ['table_section.id'], ),
            sa.ForeignKeyConstraint(['current_order_id'], ['order.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create TableBooking table
    if 'table_booking' not in existing_tables:
        op.create_table(
            'table_booking',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('table_id', sa.Integer(), nullable=False),
            sa.Column('customer_name', sa.String(128), nullable=False),
            sa.Column('customer_email', sa.String(128), nullable=True),
            sa.Column('customer_phone', sa.String(20), nullable=True),
            sa.Column('booking_date', sa.DateTime(), nullable=False),
            sa.Column('party_size', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), default='confirmed'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.ForeignKeyConstraint(['table_id'], ['table.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create KitchenPrinter table
    if 'kitchen_printer' not in existing_tables:
        op.create_table(
            'kitchen_printer',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('printer_type', sa.String(20), nullable=False),
            sa.Column('ip_address', sa.String(15), nullable=True),
            sa.Column('device_name', sa.String(128), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create OrderNote table
    if 'order_note' not in existing_tables:
        op.create_table(
            'order_note',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_item_id', sa.Integer(), nullable=False),
            sa.Column('note_type', sa.String(20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_item_id'], ['order_item.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create DelayedOrder table
    if 'delayed_order' not in existing_tables:
        op.create_table(
            'delayed_order',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('course_number', sa.Integer(), default=1),
            sa.Column('delay_minutes', sa.Integer(), default=0),
            sa.Column('sent_to_kitchen', sa.Boolean(), default=False),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create Kiosk table
    if 'kiosk' not in existing_tables:
        op.create_table(
            'kiosk',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('kiosk_code', sa.String(32), nullable=False),
            sa.Column('location', sa.String(128), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('kiosk_code', name='uix_kiosk_code')
        )

    # Create Customer table
    if 'customer' not in existing_tables:
        op.create_table(
            'customer',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('email', sa.String(128), nullable=True),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('address', sa.Text(), nullable=True),
            sa.Column('vat_number', sa.String(64), nullable=True),
            sa.Column('credit_limit', sa.Float(), default=0),
            sa.Column('outstanding_balance', sa.Float(), default=0),
            sa.Column('barcode', sa.String(128), nullable=True),
            sa.Column('registered_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('barcode', name='uix_customer_barcode')
        )

    # Create LoyaltyCard table
    if 'loyalty_card' not in existing_tables:
        op.create_table(
            'loyalty_card',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('card_number', sa.String(64), nullable=False),
            sa.Column('points_balance', sa.Integer(), default=0),
            sa.Column('tier', sa.String(20), default='standard'),
            sa.Column('points_earned_total', sa.Integer(), default=0),
            sa.Column('points_redeemed_total', sa.Integer(), default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('customer_id', name='uix_loyalty_card_customer'),
            sa.UniqueConstraint('card_number', name='uix_loyalty_card_number')
        )

    # Create LoyaltyPoints table
    if 'loyalty_points' not in existing_tables:
        op.create_table(
            'loyalty_points',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('loyalty_card_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=False),
            sa.Column('earn_method', sa.String(20), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['loyalty_card_id'], ['loyalty_card.id'], ),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create LoyaltyReward table
    if 'loyalty_reward' not in existing_tables:
        op.create_table(
            'loyalty_reward',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('points_required', sa.Integer(), nullable=False),
            sa.Column('reward_type', sa.String(20), nullable=False),
            sa.Column('reward_value', sa.Float(), nullable=True),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('stock', sa.Integer(), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create eWallet table
    if 'e_wallet' not in existing_tables:
        op.create_table(
            'e_wallet',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('balance', sa.Float(), default=0),
            sa.Column('currency', sa.String(3), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('customer_id', name='uix_ewallet_customer')
        )

    # Create eWalletTransaction table
    if 'e_wallet_transaction' not in existing_tables:
        op.create_table(
            'e_wallet_transaction',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('ewallet_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('transaction_type', sa.String(20), nullable=False),
            sa.Column('reference_id', sa.String(128), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['ewallet_id'], ['e_wallet.id'], ),
            sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create PriceList table
    if 'price_list' not in existing_tables:
        op.create_table(
            'price_list',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('pricelist_type', sa.String(20), nullable=False),
            sa.Column('valid_from', sa.DateTime(), nullable=True),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create PriceListItem table
    if 'price_list_item' not in existing_tables:
        op.create_table(
            'price_list_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('pricelist_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('price', sa.Float(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['pricelist_id'], ['price_list.id'], ),
            sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create CashierAccount table
    if 'cashier_account' not in existing_tables:
        op.create_table(
            'cashier_account',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('pin_code', sa.String(128), nullable=True),
            sa.Column('badge_id', sa.String(64), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', name='uix_cashier_user'),
            sa.UniqueConstraint('badge_id', name='uix_badge_id')
        )

    # Create CashRegister table
    if 'cash_register' not in existing_tables:
        op.create_table(
            'cash_register',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('register_name', sa.String(64), nullable=False),
            sa.Column('hardware_id', sa.String(64), nullable=True),
            sa.Column('current_cashier_id', sa.Integer(), nullable=True),
            sa.Column('opening_balance', sa.Float(), default=0),
            sa.Column('current_balance', sa.Float(), default=0),
            sa.Column('opened_at', sa.DateTime(), nullable=True),
            sa.Column('closed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(20), default='closed'),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.ForeignKeyConstraint(['current_cashier_id'], ['cashier_account.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('hardware_id', name='uix_hardware_id')
        )

    # Create CashFlow table
    if 'cash_flow' not in existing_tables:
        op.create_table(
            'cash_flow',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('cash_register_id', sa.Integer(), nullable=False),
            sa.Column('adjustment_type', sa.String(20), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('recorded_by', sa.String(64), nullable=True),
            sa.Column('expected_balance', sa.Float(), nullable=True),
            sa.Column('actual_balance', sa.Float(), nullable=True),
            sa.Column('variance', sa.Float(), nullable=True),
            sa.Column('recorded_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['cash_register_id'], ['cash_register.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create HardwareDevice table
    if 'hardware_device' not in existing_tables:
        op.create_table(
            'hardware_device',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('restaurant_id', sa.Integer(), nullable=False),
            sa.Column('device_type', sa.String(20), nullable=False),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('model', sa.String(64), nullable=True),
            sa.Column('device_id', sa.String(128), nullable=True),
            sa.Column('connection_type', sa.String(20), nullable=False),
            sa.Column('ip_address', sa.String(15), nullable=True),
            sa.Column('status', sa.String(20), default='disconnected'),
            sa.Column('last_seen', sa.DateTime(), nullable=True),
            sa.Column('active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('device_id', name='uix_device_id')
        )




def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for tbl in [
        'hardware_device', 'cash_flow', 'cash_register', 'cashier_account',
        'price_list_item', 'price_list', 'e_wallet_transaction', 'e_wallet',
        'loyalty_reward', 'loyalty_points', 'loyalty_card', 'customer',
        'kiosk', 'delayed_order', 'order_note', 'kitchen_printer',
        'table_booking', 'table', 'table_section', 'restaurant_floor_plan',
        'receipt', 'bill_split', 'discount', 'payment_transaction',
        'payment_method', 'barcode_mapping', 'product_variant', 'product',
        'product_category'
    ]:
        if tbl in existing_tables:
            op.drop_table(tbl)
