"""Baseline migration for Gaatha POS beta

Revision ID: 001_baseline
Revises: 
Create Date: 2025-12-04 13:00:00.000000

This migration represents the consolidated baseline for the v0.1.0-beta release.
It is intentionally empty because the database for existing deployments should be
created from the current models (or created by an initial schema generation),
then Alembic can be stamped to this revision.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Baseline: no operations because schema is created from models for beta.
    pass


def downgrade():
    # No-op downgrade for baseline
    pass
