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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create restaurant table
    if 'restaurant' not in existing_tables:
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
    else:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('restaurant')}
        if 'ix_restaurant_email' not in existing_indexes:
            op.create_index('ix_restaurant_email', 'restaurant', ['email'], unique=True)

    # Create store_settings table
    if 'store_settings' not in existing_tables:
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
    else:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('store_settings')}
        if 'ix_store_settings_restaurant_id' not in existing_indexes:
            op.create_index('ix_store_settings_restaurant_id', 'store_settings', ['restaurant_id'], unique=True)

    # Add columns to user table if they don't exist
    if 'user' in existing_tables or inspector.has_table('user'):
        user_cols = {col['name'] for col in inspector.get_columns('user')}
        if 'restaurant_id' not in user_cols:
            op.add_column('user', sa.Column('restaurant_id', sa.Integer(), nullable=True))
            user_fks = {fk.get('name') for fk in inspector.get_foreign_keys('user')}
            if 'fk_user_restaurant_id' not in user_fks:
                op.create_foreign_key('fk_user_restaurant_id', 'user', 'restaurant', ['restaurant_id'], ['id'])
        if 'is_super_admin' not in user_cols:
            op.add_column('user', sa.Column('is_super_admin', sa.Boolean(), nullable=False, default=False))
        if 'created_at' not in user_cols:
            op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'store_settings' in existing_tables:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('store_settings')}
        if 'ix_store_settings_restaurant_id' in existing_indexes:
            op.drop_index('ix_store_settings_restaurant_id', table_name='store_settings')
        op.drop_table('store_settings')

    if 'restaurant' in existing_tables:
        existing_indexes = {ix['name'] for ix in inspector.get_indexes('restaurant')}
        if 'ix_restaurant_email' in existing_indexes:
            op.drop_index('ix_restaurant_email', table_name='restaurant')
        op.drop_table('restaurant')

    if 'user' in existing_tables:
        user_cols = {col['name'] for col in inspector.get_columns('user')}
        user_fks = {fk.get('name') for fk in inspector.get_foreign_keys('user')}
        if 'fk_user_restaurant_id' in user_fks:
            op.drop_constraint('fk_user_restaurant_id', 'user', type_='foreignkey')
        if 'restaurant_id' in user_cols:
            op.drop_column('user', 'restaurant_id')
        if 'is_super_admin' in user_cols:
            op.drop_column('user', 'is_super_admin')
        if 'created_at' in user_cols:
            op.drop_column('user', 'created_at')
