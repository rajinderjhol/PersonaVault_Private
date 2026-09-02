from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    TESTING = "testing"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"

class Hypothesis(BaseModel):
    id: str
    environment_id: str
    statement: str  # "If we do X, we expect Y"
    premise: str    # Why we think this is true
    expected_outcome: Dict[str, Any]
    testability_criteria: List[str]
    priority: int  # Higher = more important to test
    status: HypothesisStatus
    confidence: float  # Initial confidence in hypothesis
    created_by: Optional[str] = None  # Agent or Human ID
    created_at: datetime
    updated_at: datetime
