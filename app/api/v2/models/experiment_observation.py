from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ExperimentObservation(BaseModel):
    id: str
    experiment_id: str
    observed_at: datetime
    metric_name: str
    value: float
    expected_value: float
    deviation: float
    significance: float  # Statistical significance or confidence
    metadata: Optional[Dict[str, Any]] = None
