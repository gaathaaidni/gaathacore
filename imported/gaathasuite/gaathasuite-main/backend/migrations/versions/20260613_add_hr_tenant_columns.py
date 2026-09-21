"""add tenant columns for HR models

Revision ID: 20260613_add_hr_tenant_columns
Revises: 5fc668732c41
Create Date: 2026-06-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260613_add_hr_tenant_columns'
down_revision = '5fc668732c41'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    def _add_org_id(table_name):
        try:
            cols = [c['name'] for c in insp.get_columns(table_name)]
        except Exception:
            return

        if 'organization_id' not in cols:
            op.add_column(table_name, sa.Column('organization_id', sa.Integer(), nullable=True))
            op.create_index(op.f(f'ix_{table_name}_organization_id'), table_name, ['organization_id'], unique=False)
            target_table = 'organizations' if insp.has_table('organizations') else 'organization'
            op.create_foreign_key(None, table_name, target_table, ['organization_id'], ['id'])

    if insp.has_table('department'):
        _add_org_id('department')
        
    if insp.has_table('employee'):
        _add_org_id('employee')
        
    if insp.has_table('payslip'):
        _add_org_id('payslip')
        
    if insp.has_table('performance_review'):
        _add_org_id('performance_review')


def downgrade():
    op.drop_constraint(None, 'performance_review', type_='foreignkey')
    op.drop_index(op.f('ix_performance_review_organization_id'), table_name='performance_review')
    op.drop_column('performance_review', 'organization_id')

    op.drop_constraint(None, 'payslip', type_='foreignkey')
    op.drop_index(op.f('ix_payslip_organization_id'), table_name='payslip')
    op.drop_column('payslip', 'organization_id')

    op.drop_constraint(None, 'employee', type_='foreignkey')
    op.drop_index(op.f('ix_employee_organization_id'), table_name='employee')
    op.drop_column('employee', 'organization_id')

    op.drop_constraint(None, 'department', type_='foreignkey')
    op.drop_index(op.f('ix_department_organization_id'), table_name='department')
    op.drop_column('department', 'organization_id')
