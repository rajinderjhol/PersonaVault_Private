"""add_bulk_ingestion_jobs_table

Revision ID: 27603bddbdbe
Revises: 4436f136830b
Create Date: 2026-08-31 00:37:40.491110

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27603bddbdbe'
down_revision = '4436f136830b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'bulk_ingestion_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('folder_path', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=20), default='pending'),
        sa.Column('total_files', sa.Integer(), default=0),
        sa.Column('successful_files', sa.Integer(), default=0),
        sa.Column('failed_files', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('job_metadata', sa.JSON(), default={}),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bulk_ingestion_jobs_id'), 'bulk_ingestion_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_bulk_ingestion_jobs_job_id'), 'bulk_ingestion_jobs', ['job_id'], unique=True)


def downgrade():
    op.drop_table('bulk_ingestion_jobs')
