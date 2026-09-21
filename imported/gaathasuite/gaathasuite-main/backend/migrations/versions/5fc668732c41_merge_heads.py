"""merge heads

Revision ID: 5fc668732c41
Revises: 20251217_add_coupons_orgpayments, 7e5ffd3e0afd
Create Date: 2025-12-17 13:33:48.939779

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fc668732c41'
down_revision = ('20251217_add_coupons_orgpayments', '7e5ffd3e0afd')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
