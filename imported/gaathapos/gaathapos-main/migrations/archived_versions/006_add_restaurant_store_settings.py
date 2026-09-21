"""Add Restaurant and StoreSettings models for multi-tenant support

Revision ID: 006_add_restaurant_store_settings
Revises: 005_add_tax_rules
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_restaurant_store_settings'
down_revision = '005_add_tax_rules'
branch_labels = None
depends_on = None


def upgrade():
    # Create restaurant table
    op.create_table(
        'restaurant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('email', sa.String(128), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(64), nullable=True),
        sa.Column('country', sa.String(64), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_restaurant_email')
    )
    op.create_index('ix_restaurant_email', 'restaurant', ['email'], unique=True)

    # Create store_settings table
    op.create_table(
        'store_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurant_id', sa.Integer(), nullable=False),
        sa.Column('timezone', sa.String(64), nullable=False, default='UTC'),
        sa.Column('locale', sa.String(10), nullable=False, default='en'),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('tax_region', sa.String(64), nullable=False, default='EU'),
        sa.Column('address_format', sa.String(20), nullable=False, default='standard'),
        sa.Column('business_registration', sa.String(128), nullable=True),
        sa.Column('vat_number', sa.String(64), nullable=True),
        sa.Column('payment_terms', sa.Integer(), nullable=False, default=0),
        sa.Column('invoice_prefix', sa.String(10), nullable=False, default='INV'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurant.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('restaurant_id', name='uq_store_settings_restaurant_id')
    )
    op.create_index('ix_store_settings_restaurant_id', 'store_settings', ['restaurant_id'], unique=True)

    # Add restaurant_id column to user table if it doesn't exist
    try:
        op.add_column('user', sa.Column('restaurant_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_user_restaurant_id', 'user', 'restaurant', ['restaurant_id'], ['id'])
    except Exception:
        pass  # Column might already exist from previous migration

    # Add is_super_admin column to user table if it doesn't exist
    try:
        op.add_column('user', sa.Column('is_super_admin', sa.Boolean(), nullable=False, default=False))
    except Exception:
        pass  # Column might already exist from previous migration

    # Add created_at column to user table if it doesn't exist
    try:
        op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))
    except Exception:
        pass  # Column might already exist from previous migration


def downgrade():
    op.drop_index('ix_store_settings_restaurant_id', table_name='store_settings')
    op.drop_table('store_settings')
    op.drop_index('ix_restaurant_email', table_name='restaurant')
    op.drop_table('restaurant')
    
    try:
        op.drop_constraint('fk_user_restaurant_id', 'user', type_='foreignkey')
        op.drop_column('user', 'restaurant_id')
    except Exception:
        pass
    
    try:
        op.drop_column('user', 'is_super_admin')
    except Exception:
        pass
    
    try:
        op.drop_column('user', 'created_at')
    except Exception:
        pass
