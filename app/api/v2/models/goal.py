from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class GoalStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"

class Goal(BaseModel):
    id: str
    environment_id: str
    statement: str
    description: Optional[str] = None
    sub_goals: List[str] = []  # IDs of sub-goals
    parent_goal_id: Optional[str] = None
    priority: int = 1
    success_criteria: List[Dict[str, Any]] = []
    constraints: List[str] = []
    status: GoalStatus
    owner_principal_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
