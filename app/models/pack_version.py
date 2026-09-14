"""
Pack Version Model - Track pack versions and enable rollback
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, ForeignKey, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import Base


class PackVersion(Base):
    __tablename__ = "pack_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Pack identification
    pack_id = Column(String(100), nullable=False, index=True)
    domain = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    
    # Version information
    version = Column(String(20), nullable=False)  # Semantic version: 1.0.0
    previous_version = Column(String(20), nullable=True)
    
    # Content
    pack_content = Column(JSON, nullable=False)  # Full pack YAML/JSON content
    compiled_code = Column(Text, nullable=True)  # Compiled Python code
    
    # Metadata
    description = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)
    is_rollback = Column(Boolean, default=False)
    rollback_reason = Column(Text, nullable=True)
    
    # Metrics
    events_processed = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("pack_versions.id"), nullable=True)
    children = relationship("PackVersion", 
                           remote_side=[id],
                           backref="parent",
                           foreign_keys=[parent_version_id])
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "pack_id": self.pack_id,
            "domain": self.domain,
            "name": self.name,
            "version": self.version,
            "previous_version": self.previous_version,
            "description": self.description,
            "changelog": self.changelog,
            "author": self.author,
            "is_active": self.is_active,
            "is_deprecated": self.is_deprecated,
            "is_rollback": self.is_rollback,
            "rollback_reason": self.rollback_reason,
            "events_processed": self.events_processed,
            "confidence_score": self.confidence_score,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "parent_version_id": str(self.parent_version_id) if self.parent_version_id else None
        }


class PackRollback(Base):
    __tablename__ = "pack_rollbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pack_id = Column(String(100), nullable=False, index=True)
    from_version = Column(String(20), nullable=False)
    to_version = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    successful = Column(Boolean, default=True)
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "pack_id": self.pack_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "reason": self.reason,
            "triggered_by": self.triggered_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "successful": self.successful
        }
