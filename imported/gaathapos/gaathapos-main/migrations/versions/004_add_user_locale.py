"""Add locale column to User model

Revision ID: 004_add_user_locale
Revises: 003_add_exchange_rates
Create Date: 2025-12-03 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_user_locale'
down_revision = '003_add_exchange_rates'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('user'):
        existing_cols = {col['name'] for col in inspector.get_columns('user')}
        if 'locale' not in existing_cols:
            op.add_column('user', sa.Column('locale', sa.String(10), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('user'):
        existing_cols = {col['name'] for col in inspector.get_columns('user')}
        if 'locale' in existing_cols:
            op.drop_column('user', 'locale')
