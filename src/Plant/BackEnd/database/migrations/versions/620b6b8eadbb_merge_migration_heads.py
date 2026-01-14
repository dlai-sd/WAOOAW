"""merge_migration_heads

Revision ID: 620b6b8eadbb
Revises: 0001_initial_plant_schema, 005_rls_policies
Create Date: 2026-01-14 15:30:10.472323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '620b6b8eadbb'
down_revision = ('0001_initial_plant_schema', '005_rls_policies')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
