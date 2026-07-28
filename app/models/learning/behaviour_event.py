"""
Behaviour Event Model for Decision Learning Engine.
Tracks every decision made by humans or AI.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

class BehaviourEvent(Base):
    __tablename__ = "behaviour_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Core fields
    event_type = Column(String, index=True)  # contract_review, incident_investigation
    actor = Column(String)  # user, system, AI
    artefact = Column(String)  # contract_id, incident_id
    decision = Column(String)  # approved, rejected, escalated
    reason = Column(Text)
    outcome = Column(String)  # success, failure, pending
    confidence = Column(Float, default=0.0)
    
    # Domain-specific data - renamed from 'metadata' to avoid SQLAlchemy conflict
    extra_data = Column(JSON, default={})
    
    # Learning fields
    pattern_id = Column(Integer, ForeignKey("semantic_patterns.id"), nullable=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    correction = Column(JSON, nullable=True)
    learned = Column(Boolean, default=False)
    
    # Governance
    audit_id = Column(String, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BehaviourEvent {self.event_type}: {self.decision}>"
