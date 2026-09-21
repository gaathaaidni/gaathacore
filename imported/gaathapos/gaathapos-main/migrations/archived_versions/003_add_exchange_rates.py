"""Create exchange_rate table to persist latest rates

Revision ID: 003_add_exchange_rates
Revises: 002_add_user_currency
Create Date: 2025-12-03 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_exchange_rates'
down_revision = '002_add_user_currency'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'exchange_rate',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('currency', sa.String(3), nullable=False, index=True),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('exchange_rate')
