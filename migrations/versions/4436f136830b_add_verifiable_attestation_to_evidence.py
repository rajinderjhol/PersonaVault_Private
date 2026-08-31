"""add_verifiable_attestation_to_evidence

Revision ID: 4436f136830b
Revises: 8cce013f9678
Create Date: 2026-08-31 00:33:28.429707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4436f136830b'
down_revision = '8cce013f9678'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('evidence_blocks', sa.Column('verifiable_attestation', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('evidence_blocks', 'verifiable_attestation')
