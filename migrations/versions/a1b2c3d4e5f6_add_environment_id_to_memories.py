"""add_environment_id_to_memories

Revision ID: a1b2c3d4e5f6
Revises: 5af4c8bb7471
Create Date: 2026-09-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '5af4c8bb7471'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('memories', sa.Column('environment_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_memories_environment_id'), 'memories', ['environment_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_memories_environment_id'), table_name='memories')
    op.drop_column('memories', 'environment_id')
