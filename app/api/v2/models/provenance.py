from pydantic import BaseModel
from typing import Optional

class ProvenanceRef(BaseModel):
    source_type: str
    source_id: str
    timestamp: Optional[str] = None
    hash: Optional[str] = None
