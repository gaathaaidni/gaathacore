"""Enforce tenant ownership on HR tables.

Revision ID: 20260910_hr_tenant_not_null
Revises: 303fea8f86b8
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa


revision = '20260910_hr_tenant_not_null'
down_revision = '303fea8f86b8'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    for table_name in (
        'department',
        'employee',
        'payslip',
        'attendance_record',
        'performance_review',
    ):
        if not inspector.has_table(table_name):
            continue
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if 'organization_id' not in columns:
            continue

        null_count = conn.execute(
            sa.text(f"SELECT COUNT(*) FROM {table_name} WHERE organization_id IS NULL")
        ).scalar()
        if null_count:
            raise RuntimeError(
                f"Cannot enforce NOT NULL on {table_name}.organization_id because "
                f"{null_count} rows still have NULL organization_id."
            )

        op.alter_column(
            table_name,
            'organization_id',
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade():
    for table_name in (
        'department',
        'employee',
        'payslip',
        'attendance_record',
        'performance_review',
    ):
        bind = op.get_bind()
        inspector = sa.inspect(bind)
        if inspector.has_table(table_name) and 'organization_id' in [c['name'] for c in inspector.get_columns(table_name)]:
            op.alter_column(
                table_name,
                'organization_id',
                existing_type=sa.Integer(),
                nullable=True,
            )
