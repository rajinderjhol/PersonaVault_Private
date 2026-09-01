from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from app.api.v2.models.provenance import ProvenanceRef

class ObservationStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    INVALIDATED = "invalidated"

class Observation(BaseModel):
    id: str
    environment_id: str
    event_id: Optional[str] = None
    observed_at: datetime
    observer_id: str
    content: Dict[str, Any]
    confidence: Optional[float] = None
    provenance: List[ProvenanceRef] = []
    status: ObservationStatus = ObservationStatus.CANDIDATE
