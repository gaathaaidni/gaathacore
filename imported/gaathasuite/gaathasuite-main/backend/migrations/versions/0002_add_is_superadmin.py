"""add is_superadmin column to user

Revision ID: 0002_add_is_superadmin
Revises: 2aa562de3542
Create Date: 2025-12-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_is_superadmin'
down_revision = '2aa562de3542'
branch_labels = None
depends_on = None


def upgrade():
    # add column with default False/0
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('user')]
    except Exception:
        cols = []
    if 'is_superadmin' not in cols:
        # Use a SQL boolean literal for Postgres compatibility
        op.add_column('user', sa.Column('is_superadmin', sa.Boolean(), server_default=sa.text('false')))


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('user')]
    except Exception:
        cols = []
    if 'is_superadmin' in cols:
        # SQLite doesn't support drop column; best-effort: leave as-is.
        pass
