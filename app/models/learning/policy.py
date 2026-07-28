"""
Policy Model for governing decisions.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean, ForeignKey
from datetime import datetime, timezone
from app.db.session import Base

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(String, default="1.0.0")
    domain = Column(String, index=True)
    description = Column(Text)
    
    # Policy logic
    triggers = Column(JSON, default=[])  # List of trigger patterns
    actions = Column(JSON, default=[])   # List of actions
    conditions = Column(JSON, default=[])  # Optional conditions
    
    # Learning
    confidence = Column(Float, default=0.7)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_promoted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Governance
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Policy {self.name}: confidence={self.confidence}>"
