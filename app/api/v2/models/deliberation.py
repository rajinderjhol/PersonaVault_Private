from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class Deliberation(BaseModel):
    id: str
    environment_id: str
    reasoning_chain_id: str
    alternatives: List[Dict[str, Any]]  # Different possible conclusions
    chosen_alternative: Optional[Dict[str, Any]] = None
    rationale: Optional[str] = None
    confidence: float = 0.0
    status: str = "in_progress"  # in_progress, completed
    created_at: datetime
    updated_at: datetime
