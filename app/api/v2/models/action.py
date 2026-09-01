from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class Action(BaseModel):
    id: str
    environment_id: str
    decision_id: str
    actor_id: str
    capability: str
    tool: Optional[str] = None
    parameters_hash: Optional[str] = None
    authorization_status: str
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
