"""
Device Models - Unified device management
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from typing import Dict

from app.db.session import Base
from app.mcp.device_types import DeviceType, DeviceCapability, DeviceStatus, DeviceTrustLevel


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Basic info
    device_type = Column(Enum(DeviceType), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_model = Column(String(255), nullable=True)
    device_version = Column(String(50), nullable=True)
    
    # Capabilities
    capabilities = Column(JSON, default=list)  # List of DeviceCapability
    
    # Configuration
    config = Column(JSON, default=dict)
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Trust & Security
    trust_level = Column(Enum(DeviceTrustLevel), default=DeviceTrustLevel.MEDIUM)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.PENDING)
    public_key = Column(String(4096), nullable=True)
    
    # Connectivity
    last_seen = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    endpoint = Column(String(500), nullable=True)
    
    # Metadata
    device_metadata = Column(JSON, default=dict)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "device_type": self.device_type.value,
            "device_name": self.device_name,
            "device_model": self.device_model,
            "device_version": self.device_version,
            "capabilities": [c.value for c in self.capabilities] if self.capabilities else [],
            "config": self.config,
            "user_id": str(self.user_id) if self.user_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "trust_level": self.trust_level.value,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "ip_address": self.ip_address,
            "endpoint": self.endpoint,
            "metadata": self.device_metadata,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None
        }
