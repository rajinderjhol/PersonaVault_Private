"""add_patterns_table

Revision ID: 425b230455a6
Revises: cb370c32dcfe
Create Date: 2026-08-29 21:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision = '425b230455a6'
down_revision = 'cb370c32dcfe'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create patterns table
    op.create_table(
        'patterns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('logic', JSON, nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('context', JSON, nullable=True),
        sa.Column('phase', sa.String(20), default='liquid'),
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('success_rate', sa.Float, default=0.0),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('failure_count', sa.Integer, default=0),
        sa.Column('failure_rate', sa.Float, default=0.0),
        sa.Column('age_days', sa.Integer, default=0),
        sa.Column('conflicts', sa.Integer, default=0),
        sa.Column('is_crystallized', sa.Boolean, default=False),
        sa.Column('crystallized_at', sa.DateTime, nullable=True),
        sa.Column('source_trace_ids', JSON, nullable=True),
        sa.Column('parent_pattern_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(['parent_pattern_id'], ['patterns.id'], name='fk_pattern_parent'),
    )
    op.create_index('ix_patterns_domain', 'patterns', ['domain'])
    op.create_index('ix_patterns_phase', 'patterns', ['phase'])
    op.create_index('ix_patterns_is_crystallized', 'patterns', ['is_crystallized'])
    
    # Create pattern_transitions table
    op.create_table(
        'pattern_transitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('pattern_id', UUID(as_uuid=True), nullable=False),
        sa.Column('transition_type', sa.String(50), nullable=False),
        sa.Column('from_phase', sa.String(20), nullable=True),
        sa.Column('to_phase', sa.String(20), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('transition_metadata', JSON, nullable=True),
        sa.Column('triggered_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['pattern_id'], ['patterns.id'], name='fk_transition_pattern'),
    )
    op.create_index('ix_pattern_transition_pattern', 'pattern_transitions', ['pattern_id'])
    op.create_index('ix_pattern_transition_type', 'pattern_transitions', ['transition_type'])

def downgrade() -> None:
    op.drop_table('pattern_transitions')
    op.drop_table('patterns')
