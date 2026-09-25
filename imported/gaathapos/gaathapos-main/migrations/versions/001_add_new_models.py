"""Add RolePermission, PriceHistory, AuditLog, InventoryItem models

Revision ID: 001_add_new_models
Revises: 
Create Date: 2025-12-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_new_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)"))
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create InventoryItem table
    if 'inventory_item' not in existing_tables:
        op.create_table(
            'inventory_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=True),
            sa.Column('unit', sa.String(50), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create PriceHistory table
    if 'price_history' not in existing_tables:
        op.create_table(
            'price_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('menu_item_id', sa.Integer(), nullable=False),
            sa.Column('old_price', sa.Float(), nullable=True),
            sa.Column('new_price', sa.Float(), nullable=True),
            sa.Column('changed_by', sa.String(255), nullable=True),
            sa.Column('changed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['menu_item_id'], ['menu_item.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create AuditLog table
    if 'audit_log' not in existing_tables:
        op.create_table(
            'audit_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('username', sa.String(255), nullable=True),
            sa.Column('action', sa.String(50), nullable=True),
            sa.Column('object_type', sa.String(50), nullable=True),
            sa.Column('object_id', sa.Integer(), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Create RolePermission table
    if 'role_permission' not in existing_tables:
        op.create_table(
            'role_permission',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('permission', sa.String(100), nullable=False),
            sa.Column('allowed', sa.Boolean(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('role', 'permission', name='unique_role_permission')
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for tbl in ['role_permission', 'audit_log', 'price_history', 'inventory_item']:
        if tbl in existing_tables:
            op.drop_table(tbl)
