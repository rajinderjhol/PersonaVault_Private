from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class PackType(str, Enum):
    GOVERNANCE = "governance"
    STRATEGY = "strategy"
    DOMAIN = "domain"

class V2IntelligencePack(BaseModel):
    """V2 Schema for an Intelligence Pack, wrapping a V1 Behavior Pack."""
    id: str
    name: str
    version: str
    type: PackType
    domain: str
    description: Optional[str] = None

    # V2 Ontology
    goals: List[Dict[str, Any]]
    strategies: List[Dict[str, Any]]
    policies: List[Dict[str, Any]]

    # CRITICAL: Link back to the original V1 pack
    source_behavior_pack_id: str
    
    # V2 Learning & Adaptation
    learning_rules: Optional[List[Dict[str, Any]]] = None

    # Metadata
    created_at: datetime
    updated_at: datetime
    status: str = "active"
