"""add_derived_from_to_semantic_patterns

Revision ID: 2b6430d7ed62
Revises: 097f92621c9c
Create Date: 2026-09-13 18:07:38.390213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b6430d7ed62'
down_revision = '097f92621c9c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('semantic_patterns', sa.Column('derived_from', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('semantic_patterns', 'derived_from')
