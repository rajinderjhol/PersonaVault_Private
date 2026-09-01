from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from app.api.v2.models.provenance import ProvenanceRef

class OutcomeSourceType(str, Enum):
    REAL_ACTION = "real_action"
    SIMULATION = "simulation"
    PREDICTION_EVAL = "prediction_eval"
    MANUAL_ENTRY = "manual_entry"

class Outcome(BaseModel):
    id: str
    environment_id: str
    decision_id: Optional[str] = None
    action_id: Optional[str] = None
    
    # Provenance field
    source_type: OutcomeSourceType = OutcomeSourceType.REAL_ACTION
    
    observed_at: datetime
    result: Dict[str, Any]
    success: Optional[bool] = None
    metrics: Optional[Dict[str, float]] = None
    evidence: List[ProvenanceRef] = []
    
    created_at: datetime
    updated_at: datetime
