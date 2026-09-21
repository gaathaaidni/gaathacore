"""add organization slug

Revision ID: 20260104_os
Revises: 20260103_ec
Create Date: 2026-01-03 03:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260104_os'
down_revision = '20260103_ec'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('organization')]
    except Exception:
        cols = []

    if 'slug' not in cols:
        op.add_column('organization', sa.Column('slug', sa.String(length=200), nullable=True))


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('organization')]
    except Exception:
        cols = []

    if 'slug' in cols:
        op.drop_column('organization', 'slug')
