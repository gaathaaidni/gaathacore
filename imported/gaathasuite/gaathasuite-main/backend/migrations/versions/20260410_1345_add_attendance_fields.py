"""add attendance fields

Revision ID: 202604101345
Revises: 
Create Date: 2026-04-10 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '202604101345'
down_revision = None

def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    if not insp.has_table('attendance_record'):
        return

    try:
        cols = [c['name'] for c in insp.get_columns('attendance_record')]
    except Exception:
        cols = []

    if 'organization_id' not in cols:
        op.add_column('attendance_record', sa.Column('organization_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_attendance_record_organization_id'), 'attendance_record', ['organization_id'], unique=False)
        op.create_foreign_key(None, 'attendance_record', 'organizations', ['organization_id'], ['id'])
    if 'hours_worked' not in cols:
        op.add_column('attendance_record', sa.Column('hours_worked', sa.Float(), nullable=True))
    if 'notes' not in cols:
        op.add_column('attendance_record', sa.Column('notes', sa.Text(), nullable=True))

def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table('attendance_record'):
        return

    op.drop_constraint(None, 'attendance_record', type_='foreignkey')
    op.drop_index(op.f('ix_attendance_record_organization_id'), table_name='attendance_record')
    op.drop_column('attendance_record', 'notes')
    op.drop_column('attendance_record', 'hours_worked')
    op.drop_column('attendance_record', 'organization_id')