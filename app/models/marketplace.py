from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PackStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PackCategory(str, Enum):
    CLINICAL = "clinical"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    CONTRACTS = "contracts"
    EDUCATION = "education"
    PROCUREMENT = "procurement"
    INSURANCE = "insurance"
    ROBOTICS = "robotics"
    CUSTOM = "custom"


class PackMetadata(BaseModel):
    """Metadata for an intelligence pack."""
    id: str
    name: str
    version: str
    domain: str
    description: str
    category: PackCategory
    author: str
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    status: PackStatus
    tags: List[str] = []
    icon: Optional[str] = None
    screenshots: List[str] = []
    documentation_url: Optional[str] = None
    source_url: Optional[str] = None


class PackStatistics(BaseModel):
    """Statistics for a pack."""
    download_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    use_count: int = 0
    pattern_count: int = 0
    confidence_avg: float = 0.0
    last_used: Optional[datetime] = None


class PackVersion(BaseModel):
    """Version information for a pack."""
    version: str
    released_at: datetime
    changelog: str
    download_url: str
    size_bytes: int
    min_platform_version: str
    is_latest: bool = False
    is_deprecated: bool = False


class MarketplacePack(BaseModel):
    """Complete pack information for marketplace."""
    metadata: PackMetadata
    statistics: PackStatistics
    versions: List[PackVersion]
    reviews: List[Dict[str, Any]] = []
    is_installed: bool = False
    is_owned: bool = False


class PackUploadRequest(BaseModel):
    """Request to upload a pack."""
    name: str
    domain: str
    description: str
    category: PackCategory
    tags: List[str] = []
    icon: Optional[str] = None
    version: str = "1.0.0"
    changelog: str = "Initial release"
    min_platform_version: str = "2.0.0"


class PackReviewRequest(BaseModel):
    """Request to review a pack."""
    rating: int = Field(ge=1, le=5)
    comment: str
