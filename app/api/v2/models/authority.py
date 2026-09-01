from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuthorityGrant(BaseModel):
    id: str
    environment_id: str
    principal_id: str
    capability: str
    scope: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    granted_by: Optional[str] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
