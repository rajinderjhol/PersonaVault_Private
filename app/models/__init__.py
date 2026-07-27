"""
Database models for PersonaVault.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Import the central Base from the session module to ensure metadata is shared
from app.db.session import Base
from app.models.pending_action import PendingAction

# ============ SQLAlchemy Models ============

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    # relationship
    sessions = relationship("UserSession", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    is_system = Column(Boolean, default=False)

class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True, nullable=False)
    resource_type = Column(String, index=True)
    resource_id = Column(String)
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    query = Column(Text)
    tags = Column(String, default="")
    modality = Column(String, default="text")
    embedding = Column(JSON, nullable=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_days = Column(Integer, default=0)
    is_encrypted = Column(Boolean, default=False)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    # relationship
    user = relationship("User", back_populates="sessions")

class SystemConfig(Base):
    __tablename__ = "system_configs"
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EpisodicEntry(Base):
    __tablename__ = "episodic_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=True)
    query = Column(Text)
    plan = Column(JSON)
    results = Column(JSON)
    answer = Column(Text)
    evaluation = Column(JSON, nullable=True)
    governance_receipt_id = Column(String, index=True, nullable=True)
    signature = Column(String, nullable=True)
    hitl_approved = Column(Boolean, default=False)
    user_feedback = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    consolidated = Column(Boolean, default=False)

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    resource_type = Column(String)
    resource_id = Column(Integer)
    requester_id = Column(Integer)
    approver_ids = Column(JSON) # Stored as a list of integers
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, nullable=True)

class IoTDevice(Base):
    __tablename__ = "iot_devices"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_name = Column(String)
    device_type = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default={})

class IoTData(Base):
    __tablename__ = "iot_data"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    data_type = Column(String, index=True)
    value = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    linked_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)

class MedicalAlert(Base):
    __tablename__ = "medical_alerts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String, index=True)
    severity = Column(String, default="medium")
    message = Column(Text)
    value = Column(JSON)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============ Pydantic Models (Memory Graph) ============

class MemoryCue(BaseModel):
    text: str
    type: str = Field(..., description="entity, action, time, or location")
    
    def __hash__(self):
        return hash((self.text, self.type))
    
    def __eq__(self, other):
        if not isinstance(other, MemoryCue):
            return False
        return self.text == other.text and self.type == other.type

class MemoryTag(BaseModel):
    text: str
    relation: str = Field(..., description="'mentions', 'occurred_at', 'involves', etc.")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    def __hash__(self):
        return hash((self.text, self.relation))
    
    def __eq__(self, other):
        if not isinstance(other, MemoryTag):
            return False
        return self.text == other.text and self.relation == other.relation

class MemoryContent(BaseModel):
    text: str
    type: str = Field(..., description="episodic, semantic, or topic")
    timestamp: datetime = Field(default_factory=datetime.now)
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    def __hash__(self):
        return hash((self.text, self.type, self.timestamp))
    
    def __eq__(self, other):
        if not isinstance(other, MemoryContent):
            return False
        return self.text == other.text and self.type == other.type

class RetrievalPlan(BaseModel):
    needs_retrieval: bool = True
    semantic_queries: List[str] = Field(default_factory=list)
    keyword_queries: List[str] = Field(default_factory=list)
    graph_traversals: List[str] = Field(default_factory=list)
    reasoning: str = ""
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0)

class SemanticPattern(Base):
    __tablename__ = "semantic_patterns"
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String, index=True)
    trigger = Column(Text)
    correction = Column(Text)
    success_count = Column(Integer, default=0)    # ← NEW
    weight = Column(Float, default=0.7)           # ← NEW
    is_active = Column(Boolean, default=True) # ← NEW
    occurrence_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryResult(BaseModel):
    content: str
    source: str
    score: float
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class PersonalContext(Base):
    __tablename__ = "personal_contexts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    context_type = Column(String, index=True)
    value = Column(Text)
    associated_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AISetting(Base):
    __tablename__ = "ai_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_name = Column(String, nullable=False)
    provider_type = Column(String, nullable=False)  # ollama, gemini, openai
    model_name = Column(String, nullable=False)
    deployment_type = Column(String, default="local")
    parameters = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LegalMatter(Base):
    __tablename__ = "legal_matters"
    id = Column(Integer, primary_key=True, index=True)
    matter_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_attorney_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="active")  # active, closed, pending
    priority = Column(String, default="medium")  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("legal_matters.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    document_type = Column(String)  # contract, brief, memo, etc.
    file_path = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserWidget(Base):
    __tablename__ = "user_widgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    widget_type = Column(String, nullable=False)
    config = Column(JSON, default={})
    position = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserPersona(Base):
    __tablename__ = "user_personas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    persona_type = Column(String, nullable=False)  # personal, professional, academic, etc.
    name = Column(String, nullable=False)
    description = Column(Text)
    traits = Column(JSON, default={})
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    task_type = Column(String, nullable=False)  # approval, review, research, etc.
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String, default="medium")  # low, medium, high, urgent
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Exports ============
__all__ = [
    'Base',
    'User',
    'Organization',
    'Role',
    'APIKey',
    'AuditLog',
    'Memory',
    'UserSession',
    'SystemConfig',
    'EpisodicEntry',
    'ApprovalRequest',
    'IoTDevice',
    'IoTData',
    'MedicalAlert',
    'MemoryCue',
    'MemoryTag',
    'MemoryContent',
    'RetrievalPlan',
    'SemanticPattern',
    'MemoryResult',
    'PersonalContext',
    'AISetting',
    'LegalMatter',
    'LegalDocument',
    'UserWidget',
    'UserPersona',
    'WorkflowTask',
    'PendingAction'
]
