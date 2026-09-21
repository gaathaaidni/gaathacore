"""add email confirmation columns to user

Revision ID: 20260103_ec
Revises: 5fc668732c41
Create Date: 2026-01-03 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260103_ec'
down_revision = '5fc668732c41'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = []
    try:
        cols = [c['name'] for c in insp.get_columns('user')]
    except Exception:
        pass

    if 'email_confirmed' not in cols:
        op.add_column('user', sa.Column('email_confirmed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    if 'email_confirmed_at' not in cols:
        op.add_column('user', sa.Column('email_confirmed_at', sa.DateTime(), nullable=True))


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    try:
        cols = [c['name'] for c in insp.get_columns('user')]
    except Exception:
        cols = []
    if 'email_confirmed_at' in cols:
        op.drop_column('user', 'email_confirmed_at')
    if 'email_confirmed' in cols:
        op.drop_column('user', 'email_confirmed')
