from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from datetime import datetime, timezone
from app.db.session import Base

class SemanticPattern(Base):
    __tablename__ = "semantic_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String, index=True)
    trigger = Column(Text)
    correction = Column(Text)
    occurrence_count = Column(Integer, default=1)
    success_count = Column(Integer, default=0)  # New
    weight = Column(Float, default=0.7)  # New
    is_active = Column(Boolean, default=True)  # New
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<SemanticPattern {self.pattern_type}: {self.trigger[:30]}... (weight: {self.weight})>"
