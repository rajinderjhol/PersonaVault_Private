"""add_snowflake_model

Revision ID: cb370c32dcfe
Revises: 
Create Date: 2026-08-29 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers
revision = 'cb370c32dcfe'
down_revision = None  # Replace with actual previous revision ID if known
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create snowflakes table
    op.create_table(
        'snowflakes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_pattern_id', UUID(as_uuid=True), nullable=True),
        sa.Column('parent_pattern_type', sa.String(50), nullable=True),
        sa.Column('focus', JSON, nullable=True),
        sa.Column('keywords', JSON, nullable=True),
        sa.Column('actions', JSON, nullable=True),
        sa.Column('patterns', JSON, nullable=True),
        sa.Column('rules', JSON, nullable=True),
        sa.Column('pattern_count', sa.Integer, default=0),
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('success_rate', sa.Float, default=0.0),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('pack_name', sa.String(100), nullable=True),
        sa.Column('pack_version', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_crystallized', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_snowflakes_domain', 'snowflakes', ['domain'])
    op.create_index('ix_snowflakes_parent', 'snowflakes', ['parent_pattern_id'])
    
    # Create snowflake_transitions table
    op.create_table(
        'snowflake_transitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('snowflake_id', UUID(as_uuid=True), nullable=False),
        sa.Column('transition_type', sa.String(50), nullable=False),
        sa.Column('from_phase', sa.String(20), nullable=True),
        sa.Column('to_phase', sa.String(20), nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('triggered_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['snowflake_id'], ['snowflakes.id'], name='fk_transition_snowflake'),
    )
    op.create_index('ix_transition_snowflake', 'snowflake_transitions', ['snowflake_id'])
    op.create_index('ix_transition_type', 'snowflake_transitions', ['transition_type'])

def downgrade() -> None:
    op.drop_table('snowflake_transitions')
    op.drop_table('snowflakes')
