"""
PersonaVault Data Models.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class Decision(BaseModel):
    """A decision captured by PersonaVault."""
    id: Optional[Any] = None
    domain: Optional[str] = None
    event_type: Optional[str] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None
    outcome: Optional[str] = None
    reason: Optional[str] = None
    user_id: Optional[int] = None
    actor: Optional[str] = None
    artefact: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    pattern_insights: List[Dict[str, Any]] = Field(default_factory=list)
    thought_process: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    audit_id: Optional[str] = None
    
class Pattern(BaseModel):
    """A learned pattern from past decisions."""
    id: Optional[int] = None
    type: str
    trigger: str
    correction: str
    weight: float
    confidence: float
    is_active: bool = True
    
class Memory(BaseModel):
    """A memory stored in PersonaVault."""
    id: Optional[int] = None
    content: str
    tags: List[str] = Field(default_factory=list)
    modality: str = "text"
    created_at: Optional[datetime] = None
    
class AuditLog(BaseModel):
    """An audit trail entry."""
    id: Optional[str] = None
    decision_id: str
    action: str
    actor: str
    timestamp: datetime
    details: Dict[str, Any]
