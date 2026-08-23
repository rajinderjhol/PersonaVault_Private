"""
Standardized Decision State Schema - Transport-independent.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DecisionState(BaseModel):
    """Standardized decision state for all interfaces."""
    
    # Core
    id: str
    domain: str
    event_type: str
    decision: str
    confidence: float
    outcome: str
    reason: str
    
    # Context
    user_id: int
    actor: str
    artefact: str
    
    # Metadata
    provider: Optional[str] = None
    model: Optional[str] = None
    
    # Timestamps
    detected_at: datetime
    policy_matched_at: Optional[datetime] = None
    ai_recommended_at: Optional[datetime] = None
    decision_made_at: Optional[datetime] = None
    audit_logged_at: Optional[datetime] = None
    
    # Pattern Intelligence
    pattern_insights: List[Dict[str, Any]] = Field(default_factory=list)
    pattern_applied: bool = False
    
    # Thought Process (Chain of Thought)
    thought_process: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audit
    audit_id: Optional[str] = None
    governance_receipt: Optional[str] = None
    
    # Performance
    total_time_ms: Optional[float] = None
    memory_hit_rate: Optional[float] = None
    token_efficiency: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "decision_123",
                "domain": "security",
                "event_type": "incident_response",
                "decision": "blocked",
                "confidence": 0.92,
                "outcome": "success",
                "reason": "Suspicious activity detected",
                "user_id": 1,
                "actor": "admin",
                "artefact": "firewall",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile"
            }
        }
