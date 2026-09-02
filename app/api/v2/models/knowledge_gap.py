from pydantic import BaseModel
from typing import List, Dict, Any

class KnowledgeGap(BaseModel):
    id: str
    question: str
    importance: float # 0.0 to 1.0
    evidence_needed: List[str]
    context: Dict[str, Any]
