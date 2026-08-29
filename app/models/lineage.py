"""
Data Lineage Models - Track data provenance for GDPR compliance
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SourceType(str, Enum):
    """Types of data sources in PersonaVault."""
    USER_INPUT = "user_input"
    PATTERN = "pattern"
    MEMORY = "memory"
    INTEGRATION = "integration"
    UPLOAD = "upload"


class LineageNode(BaseModel):
    """A node in the data lineage graph."""
    id: str
    type: SourceType
    created_at: datetime
    source_id: Optional[str] = None
    user_id: Optional[int] = None
    content_summary: str = Field(max_length=200)
    metadata: Dict[str, Any] = {}


class LineageEdge(BaseModel):
    """An edge connecting two lineage nodes."""
    source_node_id: str
    target_node_id: str
    relationship: str  # "created_by", "derived_from", "used_in"
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class DeletionRequest(BaseModel):
    """A user request for data deletion."""
    id: str
    user_id: int
    request_type: str  # "delete_user_data", "forget_pattern", "anonymize"
    target_ids: List[str]  # IDs of data to delete
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    audit_log: List[Dict[str, Any]] = []
    explanation: Optional[str] = None


class DeletionResult(BaseModel):
    """Result of a deletion operation."""
    request_id: str
    success: bool
    deleted_nodes: List[str] = []
    invalidated_patterns: List[str] = []
    errors: List[str] = []
    completed_at: datetime
