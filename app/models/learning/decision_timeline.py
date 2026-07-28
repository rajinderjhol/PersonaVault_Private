"""
Decision Timeline Model for tracking decision evolution.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from datetime import datetime, timezone
from app.db.session import Base

class DecisionTimeline(Base):
    __tablename__ = "decision_timelines"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("behaviour_events.id"), index=True)
    
    # Timeline steps
    step_number = Column(Integer)
    step_type = Column(String)  # detection, policy_match, ai_recommendation, human_override, decision, audit, learning
    step_label = Column(String)
    step_description = Column(Text)
    
    # Step data
    confidence = Column(Float, nullable=True)
    actor = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    extra_data = Column(JSON, default={})
    
    # Timestamp
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<DecisionTimeline step {self.step_number}: {self.step_type}>"
