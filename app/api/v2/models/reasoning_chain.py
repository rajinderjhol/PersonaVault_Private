from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class ReasoningStepType(str, Enum):
    OBSERVATION = "observation"
    ASSUMPTION = "assumption"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    EVIDENCE = "evidence"
    CONCLUSION = "conclusion"

class ReasoningStep(BaseModel):
    step_id: str
    step_type: ReasoningStepType
    content: str
    confidence: float
    evidence: List[str]  # IDs of evidence used
    dependencies: List[str]  # IDs of previous steps
    created_at: datetime

class ReasoningChain(BaseModel):
    id: str
    environment_id: str
    goal_id: str
    query: str
    steps: List[ReasoningStep]
    conclusion: Optional[str] = None
    confidence: float = 0.0
    status: str = "in_progress"  # in_progress, completed, failed
    created_by: Optional[str] = None  # Agent or Human ID
    created_at: datetime
    updated_at: datetime
