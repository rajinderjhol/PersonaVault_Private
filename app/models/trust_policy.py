from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class TrustPolicy(Base):
    __tablename__ = "trust_policies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    layer = Column(String(50), nullable=False)  # gas, liquid, ice, crystallized
    min_trust_threshold = Column(Float, nullable=False, default=0.40)
    max_trust_threshold = Column(Float, nullable=True)
    is_enforced = Column(Boolean, nullable=False, default=True)
    action_on_violation = Column(String(50), nullable=False, default="block")
    notification_enabled = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_trust_policies_user_id", "user_id"),
        Index("idx_trust_policies_layer", "layer"),
        Index("idx_trust_policies_user_layer", "user_id", "layer", unique=True),
    )
