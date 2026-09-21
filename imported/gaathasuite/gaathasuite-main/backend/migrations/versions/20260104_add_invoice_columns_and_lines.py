"""add invoice columns and invoice_line table

Revision ID: 20260104_ic
Revises: 20260104_oc
Create Date: 2026-01-03 03:55:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260104_ic'
down_revision = '20260104_oc'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('invoice')]
    except Exception:
        cols = []

    if 'number' not in cols:
        op.add_column('invoice', sa.Column('number', sa.String(length=50), nullable=True))
    if 'customer_id' not in cols:
        op.add_column('invoice', sa.Column('customer_id', sa.Integer(), nullable=True))
    if 'date' not in cols:
        op.add_column('invoice', sa.Column('date', sa.Date(), nullable=True))
    if 'due_date' not in cols:
        op.add_column('invoice', sa.Column('due_date', sa.Date(), nullable=True))
    if 'total_amount' not in cols:
        op.add_column('invoice', sa.Column('total_amount', sa.Float(), nullable=True, server_default='0'))
    if 'status' not in cols:
        op.add_column('invoice', sa.Column('status', sa.String(length=50), nullable=True, server_default='draft'))
    if 'created_at' not in cols:
        op.add_column('invoice', sa.Column('created_at', sa.DateTime(), nullable=True))
    if 'updated_at' not in cols:
        op.add_column('invoice', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Create invoice_line table if missing
    if not insp.has_table('invoice_line'):
        op.create_table(
            'invoice_line',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoice.id'), nullable=False),
            sa.Column('description', sa.String(length=300), nullable=True),
            sa.Column('qty', sa.Float(), nullable=True, server_default='1'),
            sa.Column('unit_price', sa.Float(), nullable=True, server_default='0'),
            sa.Column('total', sa.Float(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('invoice')]
    except Exception:
        cols = []

    for col in ['updated_at', 'created_at', 'status', 'total_amount', 'due_date', 'date', 'customer_id', 'number']:
        if col in cols:
            op.drop_column('invoice', col)

    if insp.has_table('invoice_line'):
        op.drop_table('invoice_line')
