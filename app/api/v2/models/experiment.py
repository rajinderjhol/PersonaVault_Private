from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class ExperimentStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Experiment(BaseModel):
    id: str
    environment_id: str
    hypothesis_id: str
    description: str
    intervention: Dict[str, Any]  # What we're doing
    control: Dict[str, Any]       # What we're comparing against
    metrics: List[str]            # What we're measuring
    status: ExperimentStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    conclusions: Optional[str] = None
    created_at: datetime
    updated_at: datetime
