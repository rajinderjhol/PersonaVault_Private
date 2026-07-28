"""
Decision Trajectory Model for tracking decision paths.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from datetime import datetime, timezone
from app.db.session import Base

class DecisionTrajectory(Base):
    __tablename__ = "decision_trajectories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Decision path
    decisions = Column(JSON, default=[])  # List of decisions
    outcomes = Column(JSON, default=[])   # List of outcomes
    context = Column(JSON, default={})
    
    # Learning
    pattern_id = Column(Integer, ForeignKey("semantic_patterns.id"), nullable=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    confidence = Column(Float, default=0.0)
    
    # Metrics
    success_score = Column(Float, default=0.0)
    time_taken = Column(Integer, default=0)  # seconds
    corrections = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<DecisionTrajectory {self.id}: success={self.success_score}>"
