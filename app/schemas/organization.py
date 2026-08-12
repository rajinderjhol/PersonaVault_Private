from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrganizationCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
