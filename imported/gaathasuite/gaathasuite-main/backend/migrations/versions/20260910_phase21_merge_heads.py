"""Merge the Phase 2 migration branches into one canonical head.

Revision ID: phase21_merge_20260910
Revises: 20260104_ic, 202604101345, 20260613_add_hr_tenant_columns, v2_schema_001, 4af2d8a7e1b3
Create Date: 2026-09-10
"""

revision = "phase21_merge_20260910"
down_revision = (
    "20260104_ic",
    "202604101345",
    "20260613_add_hr_tenant_columns",
    "v2_schema_001",
    "4af2d8a7e1b3",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass