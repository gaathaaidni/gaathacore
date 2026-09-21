"""merge multiple heads

Revision ID: 14e61ca71ed7
Revises: 001_baseline, 007_add_pos_features
Create Date: 2025-12-05 16:15:17.715079

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14e61ca71ed7'
down_revision = ('001_baseline', '007_add_pos_features')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
