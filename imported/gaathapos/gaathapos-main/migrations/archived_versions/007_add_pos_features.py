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
    # Create ProductCategory table
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

    # (truncated for brevity in archived copy)
