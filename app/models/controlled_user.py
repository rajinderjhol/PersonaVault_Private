"""
Controlled User Models - Parental controls, supervised access, compliance
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float, ForeignKey, JSON, Enum, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

from app.db.session import Base


class AccessLevel(str, enum.Enum):
    FULL = "full"          # Full access (admin)
    STANDARD = "standard"  # Regular user
    LIMITED = "limited"    # Limited access
    READ_ONLY = "read_only" # View only
    COMPLIANCE = "compliance" # Legal/healthcare compliance mode


class SupervisionMode(str, enum.Enum):
    NONE = "none"
    PARENTAL = "parental"
    LEGAL = "legal"
    HEALTHCARE = "healthcare"
    CORPORATE = "corporate"


class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"


class ControlledUser(Base):
    __tablename__ = "controlled_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Access control
    access_level = Column(Enum(AccessLevel), default=AccessLevel.STANDARD)
    supervision_mode = Column(Enum(SupervisionMode), default=SupervisionMode.NONE)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Restrictions
    allowed_domains = Column(JSON, default=list)  # ['security', 'compliance']
    max_confidence_threshold = Column(Float, default=1.0)
    requires_approval = Column(Boolean, default=False)
    
    # Time-based restrictions
    allowed_hours_start = Column(Integer, default=0)  # 0-23
    allowed_hours_end = Column(Integer, default=23)
    allowed_days = Column(JSON, default=list)  # [0,1,2,3,4,5,6] (0=Monday)
    
    # Compliance
    compliance_flags = Column(JSON, default=dict)  # {"hipaa": True, "gdpr": True}
    audit_logging = Column(Boolean, default=True)
    
    # Quota limits
    daily_decision_limit = Column(Integer, default=100)
    monthly_decision_limit = Column(Integer, default=1000)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="controlled_settings")
    supervisor = relationship("User", foreign_keys=[supervisor_id], backref="supervised_users")


class ControlledAction(Base):
    __tablename__ = "controlled_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action_type = Column(String(100), nullable=False)
    request_data = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, denied
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])


class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    connected_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], backref="connections_sent")
    connected_user = relationship("User", foreign_keys=[connected_user_id], backref="connections_received")
