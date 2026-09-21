"""add coupons and organization payments

Revision ID: 20251217_add_coupons_orgpayments
Revises: 0003_add_invitation_table
Create Date: 2025-12-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251217_add_coupons_orgpayments'
down_revision = '0003_add_invitation_table'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table('coupon'):
        op.create_table(
            'coupon',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('code', sa.String(length=100), nullable=False, unique=True),
            sa.Column('description', sa.String(length=500)),
            sa.Column('discount_type', sa.String(length=20), nullable=False, server_default='percentage'),
            sa.Column('value', sa.Float(), nullable=False, server_default='0'),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('usage_limit', sa.Integer(), nullable=True),
            sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organization.id'), nullable=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )

    # Ensure minimal 'invoice' table exists for FK references (legacy migrations may omit it)
    if not insp.has_table('invoice'):
        op.create_table(
            'invoice',
            sa.Column('id', sa.Integer(), primary_key=True),
        )

    if not insp.has_table('organization_payment'):
        op.create_table(
            'organization_payment',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organization.id'), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('method', sa.String(length=50), nullable=True),
            sa.Column('reference', sa.String(length=200), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True),
            sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoice.id'), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )
    # Ensure minimal 'invoice' table exists for FK references (legacy migrations may omit it)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table('invoice'):
        op.create_table(
            'invoice',
            sa.Column('id', sa.Integer(), primary_key=True),
        )


def downgrade():
    op.drop_table('organization_payment')
    op.drop_table('coupon')
