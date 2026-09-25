"""Add currency column to User model

Revision ID: 002_add_user_currency
Revises: 001_add_new_models
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_user_currency'
down_revision = '001_add_new_models'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('user'):
        existing_cols = {col['name'] for col in inspector.get_columns('user')}
        if 'currency' not in existing_cols:
            op.add_column('user', sa.Column('currency', sa.String(3), nullable=True, server_default='USD'))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('user'):
        existing_cols = {col['name'] for col in inspector.get_columns('user')}
        if 'currency' in existing_cols:
            op.drop_column('user', 'currency')
