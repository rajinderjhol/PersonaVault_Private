"""add_decision_traces

Revision ID: b2c3d4e5f6a7
Revises: f3dba9f10158
Create Date: 2026-08-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# Revision identifiers
revision = 'b2c3d4e5f6a7'
down_revision = 'f3dba9f10158'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing tables if they exist to start fresh with correct foreign keys
    op.execute('DROP TABLE IF EXISTS provenance_records')
    op.execute('DROP TABLE IF EXISTS decision_traces')
    
    # Decision traces table
    op.create_table(
        'decision_traces',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_sessions.id'), nullable=True),
        sa.Column('message_id', sa.Integer(), sa.ForeignKey('chat_messages.id'), nullable=True),
        sa.Column('step', sa.Enum('perception', 'policy_match', 'ai_recommendation', 'action', 'outcome', 'summary', name='tracestep'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('is_crystallized', sa.Boolean(), default=False),
        
        # New fields for orchestrator compatibility
        sa.Column('decision_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('query', sa.String(), nullable=True),
        sa.Column('response', sa.String(), nullable=True),
        sa.Column('trace', sa.JSON(), nullable=True),
        sa.Column('explanation', sa.String(), nullable=True),
        sa.Column('pack_name', sa.String(), nullable=True),
        sa.Column('pack_version', sa.String(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
    )
    
    # Provenance records table
    op.create_table(
        'provenance_records',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('trace_id', sa.UUID(), sa.ForeignKey('decision_traces.id'), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('source_text', sa.String(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('receipt_hash', sa.String(), nullable=True),
    )
    
    # Indexes for performance
    op.create_index('idx_decision_traces_session', 'decision_traces', ['session_id'])
    op.create_index('idx_decision_traces_step', 'decision_traces', ['step'])
    op.create_index('idx_decision_traces_decision_id', 'decision_traces', ['decision_id'])
    op.create_index('idx_provenance_trace', 'provenance_records', ['trace_id'])

def downgrade():
    op.drop_table('provenance_records')
    op.drop_table('decision_traces')
    op.execute('DROP TYPE tracestep')
