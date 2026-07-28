"""
Behaviour Pack Model for declarative domain configuration.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from datetime import datetime, timezone
from app.db.session import Base

class BehaviourPack(Base):
    __tablename__ = "behaviour_packs"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(String, default="1.0.0")
    domain = Column(String, index=True)
    description = Column(Text)
    
    # Configuration
    entities = Column(JSON, default=[])
    events = Column(JSON, default=[])
    decision_types = Column(JSON, default=[])
    metrics = Column(JSON, default=[])
    prompts = Column(JSON, default={})
    views = Column(JSON, default={})
    policies = Column(JSON, default=[])
    evaluation_rules = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    installed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    installed_by = Column(Integer, default=1)  # Default to admin user
    
    def __repr__(self):
        return f"<BehaviourPack {self.name} ({self.domain})>"
