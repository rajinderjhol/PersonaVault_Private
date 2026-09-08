from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base


class IntelligenceSource(Base):
    __tablename__ = "intelligence_sources"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    
    trust_score = Column(Float, nullable=False, default=0.50)
    trust_level = Column(String(20), nullable=False, default="BASIC")
    trust_history = Column(JSON, nullable=False, default=list)
    
    contribution_metrics = Column(JSON, nullable=False, default=dict)
    memory_access = Column(JSON, nullable=False, default=list)
    
    status = Column(String(20), nullable=False, default="active")
    last_contribution = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, nullable=False, server_default=func.now())
    
    extra_metadata = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="intelligence_sources")
    
    __table_args__ = (
        Index("idx_intelligence_sources_user_id", "user_id"),
        Index("idx_intelligence_sources_status", "status"),
        Index("idx_intelligence_sources_trust_score", "trust_score"),
        Index("idx_intelligence_sources_type", "type"),
    )
