from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserProfileCreate(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    active_persona: Optional[str] = "default"
    workspace_config: Optional[Dict[str, Any]] = None

class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    preferences: Dict[str, Any]
    active_persona: str
    workspace_config: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True
