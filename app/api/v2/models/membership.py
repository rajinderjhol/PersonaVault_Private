from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class MembershipStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ENDED = "ended"

class Membership(BaseModel):
    id: str
    environment_id: str
    principal_id: str
    role: Optional[str] = None
    authority_level: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: MembershipStatus = MembershipStatus.ACTIVE
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
