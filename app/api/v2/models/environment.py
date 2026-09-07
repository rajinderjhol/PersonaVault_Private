from pydantic import BaseModel, Field
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
    type: str = "standard"
    name: str
    description: Optional[str] = None
    owner_principal_id: str = "1"
    parent_environment_id: Optional[str] = None
    status: EnvironmentStatus = EnvironmentStatus.ACTIVE
    mode: str = "standard"
    
    # Governance & Sensitivity
    max_sensitivity: SensitivityClassification = SensitivityClassification.INTERNAL
    allowed_abstraction_levels: List[AbstractionLevel] = [
        AbstractionLevel.GENERALIZED,
        AbstractionLevel.STRATEGIC,
        AbstractionLevel.PRINCIPLE
    ]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
