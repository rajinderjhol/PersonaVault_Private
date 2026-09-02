from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from app.api.v2.models.transfer import SensitivityClassification, AbstractionLevel

class EnvironmentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    SIMULATION = "simulation"
    ARCHIVED = "archived"

class Environment(BaseModel):
    id: str
    type: str
    name: str
    description: Optional[str] = None
    owner_principal_id: str
    parent_environment_id: Optional[str] = None
    status: EnvironmentStatus
    mode: str = "standard"  # standard, restricted, simulation, audit
    
    # Governance & Sensitivity
    max_sensitivity: SensitivityClassification = SensitivityClassification.INTERNAL
    allowed_abstraction_levels: List[AbstractionLevel] = [
        AbstractionLevel.GENERALIZED,
        AbstractionLevel.STRATEGIC,
        AbstractionLevel.PRINCIPLE
    ]
    
    created_at: datetime
    updated_at: datetime
