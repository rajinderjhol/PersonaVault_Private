"""Add intelligence_sources table

Revision ID: 20260909_001
Revises: 5af4c8bb7471
Create Date: 2026-09-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

revision = '20260909_001'
down_revision = '5af4c8bb7471'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'intelligence_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('trust_score', sa.Float, nullable=False, server_default='0.50'),
        sa.Column('trust_level', sa.String(20), nullable=False, server_default='BASIC'),
        sa.Column('trust_history', JSON, nullable=False, server_default='[]'),
        sa.Column('contribution_metrics', JSON, nullable=False, server_default='{"patterns_crystallized":0,"reasoning_steps_validated":0,"memory_matches_contributed":0,"decision_traces_triggered":0,"events_ingested":0}'),
        sa.Column('memory_access', JSON, nullable=False, server_default='["gas"]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('last_contribution', sa.DateTime, nullable=True),
        sa.Column('registered_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('extra_metadata', JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_intelligence_sources_user_id', 'intelligence_sources', ['user_id'])
    op.create_index('idx_intelligence_sources_status', 'intelligence_sources', ['status'])
    op.create_index('idx_intelligence_sources_trust_score', 'intelligence_sources', ['trust_score'])
    op.create_index('idx_intelligence_sources_type', 'intelligence_sources', ['type'])


def downgrade():
    op.drop_table('intelligence_sources')
