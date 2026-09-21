"""add missing organization columns

Revision ID: 20260104_oc
Revises: 20260104_os
Create Date: 2026-01-03 03:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260104_oc'
down_revision = '20260104_os'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('organization')]
    except Exception:
        cols = []

    if 'domain' not in cols:
        op.add_column('organization', sa.Column('domain', sa.String(length=200), nullable=True))
    if 'logo_url' not in cols:
        op.add_column('organization', sa.Column('logo_url', sa.String(length=500), nullable=True))
    if 'timezone' not in cols:
        op.add_column('organization', sa.Column('timezone', sa.String(length=50), nullable=True, server_default='UTC'))
    if 'currency' not in cols:
        op.add_column('organization', sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'))
    if 'is_active' not in cols:
        op.add_column('organization', sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')))
    if 'subscription_id' not in cols:
        op.add_column('organization', sa.Column('subscription_id', sa.Integer(), nullable=True))
    if 'created_at' not in cols:
        op.add_column('organization', sa.Column('created_at', sa.DateTime(), nullable=True))
    if 'updated_at' not in cols:
        op.add_column('organization', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('organization')]
    except Exception:
        cols = []

    for col in ['updated_at', 'created_at', 'subscription_id', 'is_active', 'currency', 'timezone', 'logo_url', 'domain']:
        if col in cols:
            op.drop_column('organization', col)
