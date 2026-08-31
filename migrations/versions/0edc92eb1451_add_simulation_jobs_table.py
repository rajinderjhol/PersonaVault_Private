"""add_simulation_jobs_table

Revision ID: 0edc92eb1451
Revises: 27603bddbdbe
Create Date: 2026-08-31 00:46:00.329587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0edc92eb1451'
down_revision = '27603bddbdbe'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'simulation_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('domain', sa.String(length=50), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), default='pending'),
        sa.Column('result_metrics', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('attestation', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_simulation_jobs_id'), 'simulation_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_simulation_jobs_job_id'), 'simulation_jobs', ['job_id'], unique=True)


def downgrade():
    op.drop_table('simulation_jobs')
