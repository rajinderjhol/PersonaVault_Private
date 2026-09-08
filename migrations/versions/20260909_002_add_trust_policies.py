"""Add trust_policies table

Revision ID: 20260909_002
Revises: 20260909_001
Create Date: 2026-09-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = '20260909_002'
down_revision = '20260909_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'trust_policies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('layer', sa.String(50), nullable=False, unique=True),
        sa.Column('min_trust_threshold', sa.Float, nullable=False, server_default='0.40'),
        sa.Column('max_trust_threshold', sa.Float, nullable=True),
        sa.Column('is_enforced', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('action_on_violation', sa.String(50), nullable=False, server_default='block'),
        sa.Column('notification_enabled', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_trust_policies_user_id', 'trust_policies', ['user_id'])
    op.create_index('idx_trust_policies_layer', 'trust_policies', ['layer'])


def downgrade():
    op.drop_table('trust_policies')
