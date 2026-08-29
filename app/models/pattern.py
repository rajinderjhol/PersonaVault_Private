"""
Pattern Model - Core intelligence patterns with thermodynamic phase tracking
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from app.db.session import Base


class PatternPhase(str, enum.Enum):
    """Thermodynamic phases for patterns"""
    GAS = "gas"
    LIQUID = "liquid"
    ICE = "ice"
    SNOWFLAKE = "snowflake"


class PatternType(str, enum.Enum):
    """Types of patterns"""
    DECISION = "decision"
    REASONING = "reasoning"
    RESPONSE = "response"
    ROUTING = "routing"
    DOMAIN = "domain"


class Pattern(Base):
    """Core pattern model with thermodynamic phase tracking"""
    __tablename__ = "patterns"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    pattern_type = Column(String(50), default="decision")
    domain = Column(String(100), nullable=True, index=True)
    
    # Content
    logic = Column(JSON, nullable=True)  # The actual pattern logic/rules
    reasoning = Column(Text, nullable=True)  # Reasoning behind the pattern
    context = Column(JSON, nullable=True)  # Context where pattern applies
    template = Column(Text, nullable=True)  # Response template
    
    # Thermodynamic phase tracking
    phase = Column(String(20), default="liquid", index=True)
    phase_updated_at = Column(DateTime, nullable=True)
    
    # Performance metrics
    confidence = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    use_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    failure_rate = Column(Float, default=0.0)
    age_days = Column(Integer, default=0)
    conflicts = Column(Integer, default=0)
    
    # Crystallization
    is_crystallized = Column(Boolean, default=False, index=True)
    crystallized_at = Column(DateTime, nullable=True)
    crystallization_confidence = Column(Float, default=0.0)
    
    # Sources
    source_trace_ids = Column(JSON, nullable=True)  # DecisionTrace IDs
    source_session_id = Column(Integer, nullable=True)
    source_user_id = Column(Integer, nullable=True)
    
    # Hierarchy (for pattern evolution)
    parent_pattern_id = Column(UUID(as_uuid=True), ForeignKey("patterns.id"), nullable=True)
    version = Column(Integer, default=1)
    
    # Behavior pack reference
    pack_name = Column(String(100), nullable=True)
    pack_version = Column(String(20), nullable=True)
    
    # Snowflake specific fields (when phase = snowflake)
    snowflake_domain = Column(String(100), nullable=True)
    snowflake_focus = Column(JSON, nullable=True)
    snowflake_keywords = Column(JSON, nullable=True)
    snowflake_actions = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    
    # Relationships
    children = relationship("Pattern", 
                           remote_side=[id],
                           backref="parent",
                           foreign_keys=[parent_pattern_id])
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "domain": self.domain,
            "logic": self.logic,
            "reasoning": self.reasoning,
            "context": self.context,
            "template": self.template,
            "phase": self.phase,
            "phase_updated_at": self.phase_updated_at.isoformat() if self.phase_updated_at else None,
            "confidence": self.confidence,
            "success_rate": self.success_rate,
            "use_count": self.use_count,
            "failure_count": self.failure_count,
            "failure_rate": self.failure_rate,
            "age_days": self.age_days,
            "conflicts": self.conflicts,
            "is_crystallized": self.is_crystallized,
            "crystallized_at": self.crystallized_at.isoformat() if self.crystallized_at else None,
            "crystallization_confidence": self.crystallization_confidence,
            "source_trace_ids": self.source_trace_ids,
            "source_session_id": self.source_session_id,
            "source_user_id": self.source_user_id,
            "parent_pattern_id": str(self.parent_pattern_id) if self.parent_pattern_id else None,
            "version": self.version,
            "pack_name": self.pack_name,
            "pack_version": self.pack_version,
            "snowflake_domain": self.snowflake_domain,
            "snowflake_focus": self.snowflake_focus,
            "snowflake_keywords": self.snowflake_keywords,
            "snowflake_actions": self.snowflake_actions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None
        }
    
    def to_summary(self) -> dict:
        """Convert to summary for list views"""
        return {
            "id": str(self.id),
            "name": self.name,
            "domain": self.domain,
            "phase": self.phase,
            "confidence": self.confidence,
            "success_rate": self.success_rate,
            "use_count": self.use_count,
            "is_crystallized": self.is_crystallized,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PatternTransition(Base):
    """Track pattern phase transitions for thermodynamic analysis"""
    __tablename__ = "pattern_transitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pattern_id = Column(UUID(as_uuid=True), ForeignKey("patterns.id"), nullable=False)
    
    transition_type = Column(String(50), nullable=False)  # freeze, melt, evaporate, sublimate, branch
    from_phase = Column(String(20), nullable=True)
    to_phase = Column(String(20), nullable=True)
    
    reason = Column(Text, nullable=True)
    transition_metadata = Column(JSON, nullable=True)
    triggered_by = Column(String(100), nullable=True)  # agent_id, system, user_id
    
    # Performance impact
    confidence_delta = Column(Float, default=0.0)
    success_delta = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    pattern = relationship("Pattern", backref="transitions")
    
    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "pattern_id": str(self.pattern_id),
            "transition_type": self.transition_type,
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "reason": self.reason,
            "transition_metadata": self.transition_metadata,
            "triggered_by": self.triggered_by,
            "confidence_delta": self.confidence_delta,
            "success_delta": self.success_delta,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
