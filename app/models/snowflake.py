"""
Snowflake Model - Domain-specific pattern variants
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, ForeignKey, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import Base
from app.models.pattern import Pattern

class Snowflake(Base):
    __tablename__ = "snowflakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Core fields
    domain = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Reference to base pattern
    parent_pattern_id = Column(UUID(as_uuid=True), ForeignKey("patterns.id"), nullable=True)
    parent_pattern_type = Column(String(50), nullable=True)  # ice, liquid, etc.
    
    # Domain specialization
    focus = Column(JSON, nullable=True)  # List of focus areas
    keywords = Column(JSON, nullable=True)  # Domain-specific keywords
    actions = Column(JSON, nullable=True)  # Domain-specific actions
    patterns = Column(JSON, nullable=True)  # Domain-specific patterns
    rules = Column(JSON, nullable=True)  # Domain-specific rules
    
    # Metrics
    pattern_count = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    use_count = Column(Integer, default=0)
    
    # Behavior pack reference
    pack_name = Column(String(100), nullable=True)
    pack_version = Column(String(20), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_crystallized = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to base pattern
    base_pattern = relationship("Pattern", foreign_keys=[parent_pattern_id])
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "domain": self.domain,
            "name": self.name,
            "description": self.description,
            "parent_pattern_id": str(self.parent_pattern_id) if self.parent_pattern_id else None,
            "parent_pattern_type": self.parent_pattern_type,
            "focus": self.focus or [],
            "keywords": self.keywords or [],
            "actions": self.actions or [],
            "patterns": self.patterns or [],
            "rules": self.rules or [],
            "pattern_count": self.pattern_count,
            "confidence": self.confidence,
            "success_rate": self.success_rate,
            "use_count": self.use_count,
            "pack_name": self.pack_name,
            "pack_version": self.pack_version,
            "is_active": self.is_active,
            "is_crystallized": self.is_crystallized,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class SnowflakeTransition(Base):
    """Track snowflake phase transitions."""
    __tablename__ = "snowflake_transitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    snowflake_id = Column(UUID(as_uuid=True), ForeignKey("snowflakes.id"), nullable=False)
    
    transition_type = Column(String(50), nullable=False)  # freeze, melt, evaporate, sublimate, branch
    from_phase = Column(String(20), nullable=True)
    to_phase = Column(String(20), nullable=True)
    
    transition_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'
    triggered_by = Column(String(100), nullable=True)  # agent_id or user_id
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    snowflake = relationship("Snowflake", backref="transitions")
