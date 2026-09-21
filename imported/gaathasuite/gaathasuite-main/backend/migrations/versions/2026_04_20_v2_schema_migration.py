"""transition legacy tables to sqlalchemy 2.0 async schema

Revision ID: v2_schema_001
Revises: 
Create Date: 2026-04-20 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'v2_schema_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Update 'user' table
    if 'user' in tables and 'is_active' not in [c['name'] for c in inspector.get_columns('user')]:
        op.add_column('user', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    # Note: timestamps are already present, but we ensure they are handled by the new Base
    
    # 2. Update 'leads' table for multi-tenancy and async compatibility
    if 'leads' in tables:
        leads_cols = [c['name'] for c in inspector.get_columns('leads')]
        if 'organization_id' not in leads_cols:
            op.add_column('leads', sa.Column('organization_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_leads_organization_id'), 'leads', ['organization_id'], unique=False)
        if 'updated_at' not in leads_cols:
            op.add_column('leads', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
        if 'is_active' not in leads_cols:
            op.add_column('leads', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

    # 3. Update 'customers' table
    if 'customers' in tables:
        cust_cols = [c['name'] for c in inspector.get_columns('customers')]
        if 'organization_id' not in cust_cols:
            op.add_column('customers', sa.Column('organization_id', sa.Integer(), nullable=True))
            op.create_index(op.f('ix_customers_organization_id'), 'customers', ['organization_id'], unique=False)
        if 'is_active' not in cust_cols:
            op.add_column('customers', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))
    
    # 4. Update 'invoice' table (renaming might be needed depending on legacy state, 
    # but here we focus on adding missing columns)
    if 'invoice' in tables and 'is_active' not in [c['name'] for c in inspector.get_columns('invoice')]:
        op.add_column('invoice', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

    # Optional: If you haven't seeded default orgs, you might want to set a default org_id
    # op.execute("UPDATE leads SET organization_id = 1")
    # op.alter_column('leads', 'organization_id', nullable=False)

def downgrade():
    op.drop_column('invoice', 'is_active')
    op.drop_index(op.f('ix_customers_organization_id'), table_name='customers')
    op.drop_column('customers', 'is_active')
    op.drop_column('customers', 'organization_id')
    op.drop_column('leads', 'is_active')
    op.drop_column('leads', 'updated_at')
    op.drop_index(op.f('ix_leads_organization_id'), table_name='leads')
    op.drop_column('leads', 'organization_id')
    op.drop_column('user', 'is_active')