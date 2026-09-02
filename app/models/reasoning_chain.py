from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class ReasoningChainModel(Base):
    __tablename__ = "reasoning_chains"
    
    id = Column(String, primary_key=True)
    environment_id = Column(String, nullable=False)
    goal_id = Column(String, nullable=False)
    query = Column(String, nullable=False)
    steps = Column(JSON, nullable=False)
    conclusion = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String, default="in_progress")
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "environment_id": self.environment_id,
            "goal_id": self.goal_id,
            "query": self.query,
            "steps": self.steps,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
