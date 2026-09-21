"""Add TaxRule model for tax fiscalization

Revision ID: 005_add_tax_rules
Revises: 004_add_user_locale
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_tax_rules'
down_revision = '004_add_user_locale'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tax_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('region', sa.String(64), nullable=False),
        sa.Column('tax_type', sa.String(32), nullable=False),  # VAT, GST, SALES_TAX, etc.
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('inclusive', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('region', 'tax_type', name='uq_tax_rule_region_type')
    )


def downgrade():
    op.drop_table('tax_rule')
