from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class PrincipalType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    TEAM = "team"
    FAMILY = "family"
    INSTITUTION = "institution"
    AGENT = "agent"
    SERVICE = "service"
    DEVICE = "device"

class PrincipalStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Principal(BaseModel):
    id: str
    type: PrincipalType
    name: str
    status: PrincipalStatus = PrincipalStatus.ACTIVE
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
