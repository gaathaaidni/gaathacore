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
    # Add currency column to user table
    op.add_column('user', sa.Column('currency', sa.String(3), nullable=True, server_default='USD'))


def downgrade():
    # Remove currency column from user table
    op.drop_column('user', 'currency')
