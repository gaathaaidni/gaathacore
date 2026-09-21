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
    op.add_column('user', sa.Column('locale', sa.String(10), nullable=True))


def downgrade():
    op.drop_column('user', 'locale')
