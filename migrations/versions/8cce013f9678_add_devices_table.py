"""add_devices_table

Revision ID: 8cce013f9678
Revises: 4e6c90c460fa
Create Date: 2026-08-30 21:02:27.912128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8cce013f9678'
down_revision = '4e6c90c460fa'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'devices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('device_type', sa.Enum('iot', 'robot', 'medical', 'camera', 'edge', 'enterprise', 'smart_home', 'wearable', 'network', 'unknown', name='devicetype'), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=False),
        sa.Column('device_model', sa.String(255), nullable=True),
        sa.Column('device_version', sa.String(50), nullable=True),
        sa.Column('capabilities', sa.JSON, nullable=True),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('trust_level', sa.Enum('full', 'high', 'medium', 'low', 'untrusted', name='devicetrustlevel'), nullable=False),
        sa.Column('status', sa.Enum('online', 'offline', 'degraded', 'maintenance', 'pending', 'unknown', name='devicestatus'), nullable=False),
        sa.Column('public_key', sa.String(4096), nullable=True),
        sa.Column('last_seen', sa.DateTime, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('registered_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table('devices')
