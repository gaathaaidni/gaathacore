"""add invitation table

Revision ID: 0003_add_invitation_table
Revises: 0002_add_is_superadmin
Create Date: 2025-12-17 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_invitation_table'
down_revision = '0002_add_is_superadmin'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if not insp.has_table('invitation'):
        # Ensure a minimal 'organization' table exists for the foreign key
        if not insp.has_table('organization'):
            op.create_table(
                'organization',
                sa.Column('id', sa.Integer(), primary_key=True),
                sa.Column('name', sa.String(length=200), nullable=True),
            )
        op.create_table(
            'invitation',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organization.id'), nullable=False),
            sa.Column('email', sa.String(length=200), nullable=False),
            sa.Column('token', sa.String(length=128), nullable=False, unique=True),
            sa.Column('role', sa.String(length=50), nullable=True),
            sa.Column('invited_by', sa.Integer(), sa.ForeignKey('user.id')),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )


def downgrade():
    op.drop_table('invitation')
