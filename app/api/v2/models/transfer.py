from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime
from app.api.v2.models.provenance import ProvenanceRef

class SensitivityClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SENSITIVE = "sensitive"

class AbstractionLevel(str, Enum):
    RAW = "raw"
    GENERALIZED = "generalized"
    STRATEGIC = "strategic"
    PRINCIPLE = "principle"

class TransferCandidate(BaseModel):
    id: str
    source_environment_id: str
    target_environment_id: Optional[str] = None
    
    # The payload (e.g., Crystallized Pattern)
    pattern_id: str
    
    # Governed attributes
    sensitivity: SensitivityClassification = SensitivityClassification.INTERNAL
    abstraction_level: AbstractionLevel = AbstractionLevel.GENERALIZED
    
    # Integrity
    provenance_chain: List[ProvenanceRef] = []
    
    # State
    status: str = "proposed" # proposed, validated, authorized, transferred, rejected
    created_at: datetime = datetime.utcnow()
