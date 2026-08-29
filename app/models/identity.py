"""
Identity Models - User profiles, devices, permissions, trust
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class DeviceType(str, Enum):
    """Types of devices."""
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    CLI = "cli"
    API = "api"
    UNKNOWN = "unknown"


class DeviceTrustLevel(str, Enum):
    """Trust levels for devices."""
    UNTRUSTED = "untrusted"
    BASIC = "basic"
    TRUSTED = "trusted"
    VERIFIED = "verified"


class UserProfile(BaseModel):
    """Complete user profile."""
    id: int
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    preferences: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class Device(BaseModel):
    """Device registered to a user."""
    id: str
    user_id: int
    name: str
    type: DeviceType
    trust_level: DeviceTrustLevel = DeviceTrustLevel.BASIC
    last_seen: Optional[datetime] = None
    created_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    public_key: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_active: bool = True
    is_verified: bool = False


class PermissionLevel(str, Enum):
    """Permission levels for actions."""
    OBSERVE = "observe"
    SUGGEST = "suggest"
    PREPARE = "prepare"
    ASK = "ask"
    EXECUTE = "execute"
    AUTONOMOUS = "autonomous"


class Permission(BaseModel):
    """User permission for an action."""
    user_id: int
    action: str
    level: PermissionLevel
    granted_at: datetime
    expires_at: Optional[datetime] = None
    granted_by: Optional[int] = None
    metadata: Dict[str, Any] = {}


class TrustedEntity(BaseModel):
    """Trusted entity (device, app, person)."""
    id: str
    user_id: int
    entity_type: str  # "device", "app", "person", "service"
    entity_id: str
    trust_level: float  # 0.0 - 1.0
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class SyncState(BaseModel):
    """Multi-device sync state."""
    user_id: int
    device_id: str
    last_sync_at: datetime
    sync_version: str
    memory_hash: Optional[str] = None
    patterns_hash: Optional[str] = None
    context_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}
