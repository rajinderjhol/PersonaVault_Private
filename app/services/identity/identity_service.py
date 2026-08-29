"""
Identity Service - Manage user profiles, devices, permissions, trust
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from app.models.identity import (
    UserProfile, Device, DeviceType, DeviceTrustLevel,
    Permission, PermissionLevel, TrustedEntity, SyncState
)

logger = logging.getLogger(__name__)


class IdentityService:
    """
    Complete identity management service.
    """
    
    def __init__(self):
        self.data_path = Path("data/identity")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load identity data from disk."""
        self.profiles = {}
        self.devices = {}
        self.permissions = {}
        self.trusted = {}
        self.sync_states = {}
        
        # Load from disk if exists
        self._load_json("profiles", self.profiles)
        self._load_json("devices", self.devices)
        self._load_json("permissions", self.permissions)
        self._load_json("trusted", self.trusted)
        self._load_json("sync_states", self.sync_states)
    
    def _load_json(self, name: str, target: dict):
        """Load JSON data from disk."""
        path = self.data_path / f"{name}.json"
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    target.update(data)
            except Exception as e:
                logger.error(f"Failed to load {name}: {e}")
    
    def _save_json(self, name: str, data: dict):
        """Save JSON data to disk."""
        path = self.data_path / f"{name}.json"
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save {name}: {e}")
    
    # ================================================================
    # User Profiles
    # ================================================================
    
    async def create_profile(
        self,
        username: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(
            id=len(self.profiles) + 1,
            username=username,
            email=email,
            full_name=full_name,
            display_name=full_name or username,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            preferences=kwargs.get("preferences", {}),
            settings=kwargs.get("settings", {})
        )
        
        self.profiles[str(profile.id)] = profile.dict()
        self._save_json("profiles", self.profiles)
        
        logger.info(f"Created profile for user {profile.id}: {username}")
        return profile
    
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get a user profile."""
        profile_data = self.profiles.get(str(user_id))
        if profile_data:
            return UserProfile(**profile_data)
        return None
    
    async def update_profile(self, user_id: int, **kwargs) -> Optional[UserProfile]:
        """Update a user profile."""
        profile_data = self.profiles.get(str(user_id))
        if not profile_data:
            return None
        
        profile = UserProfile(**profile_data)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        self.profiles[str(user_id)] = profile.dict()
        self._save_json("profiles", self.profiles)
        
        return profile
    
    # ================================================================
    # Device Management
    # ================================================================
    
    async def register_device(
        self,
        user_id: int,
        name: str,
        device_type: DeviceType = DeviceType.WEB,
        metadata: Optional[Dict] = None
    ) -> Device:
        """Register a new device for a user."""
        device = Device(
            id=f"dev_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            name=name,
            type=device_type,
            trust_level=DeviceTrustLevel.BASIC,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        if device.id not in self.devices:
            self.devices[device.id] = {}
        self.devices[device.id][str(user_id)] = device.dict()
        self._save_json("devices", self.devices)
        
        logger.info(f"Registered device {device.id} for user {user_id}")
        return device
    
    async def get_devices(self, user_id: int) -> List[Device]:
        """Get all devices for a user."""
        devices = []
        for device_id, user_devices in self.devices.items():
            if str(user_id) in user_devices:
                devices.append(Device(**user_devices[str(user_id)]))
        return devices
    
    async def get_device(self, device_id: str, user_id: int) -> Optional[Device]:
        """Get a specific device."""
        if device_id in self.devices:
            device_data = self.devices[device_id].get(str(user_id))
            if device_data:
                return Device(**device_data)
        return None
    
    async def update_device(
        self,
        device_id: str,
        user_id: int,
        **kwargs
    ) -> Optional[Device]:
        """Update a device."""
        device_data = self.devices.get(device_id, {}).get(str(user_id))
        if not device_data:
            return None
        
        device = Device(**device_data)
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)
        
        device.last_seen = datetime.now()
        self.devices[device_id][str(user_id)] = device.dict()
        self._save_json("devices", self.devices)
        
        return device
    
    async def trust_device(
        self,
        device_id: str,
        user_id: int,
        trust_level: DeviceTrustLevel
    ) -> Optional[Device]:
        """Set trust level for a device."""
        return await self.update_device(device_id, user_id, trust_level=trust_level)
    
    # ================================================================
    # Permission System
    # ================================================================
    
    async def grant_permission(
        self,
        user_id: int,
        action: str,
        level: PermissionLevel,
        granted_by: Optional[int] = None,
        expires_in_days: Optional[int] = None
    ) -> Permission:
        """Grant a permission to a user."""
        permission = Permission(
            user_id=user_id,
            action=action,
            level=level,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
            granted_by=granted_by
        )
        
        key = f"{user_id}:{action}"
        self.permissions[key] = permission.dict()
        self._save_json("permissions", self.permissions)
        
        logger.info(f"Granted {level.value} permission for {action} to user {user_id}")
        return permission
    
    async def check_permission(
        self,
        user_id: int,
        action: str,
        required_level: PermissionLevel
    ) -> bool:
        """Check if a user has permission for an action."""
        key = f"{user_id}:{action}"
        permission_data = self.permissions.get(key)
        
        if not permission_data:
            return False
        
        permission = Permission(**permission_data)
        
        # Check expiration
        if permission.expires_at and permission.expires_at < datetime.now():
            return False
        
        # Check level (higher level = more permission)
        levels = list(PermissionLevel)
        required_idx = levels.index(required_level)
        granted_idx = levels.index(permission.level)
        
        return granted_idx >= required_idx
    
    async def revoke_permission(self, user_id: int, action: str) -> bool:
        """Revoke a permission."""
        key = f"{user_id}:{action}"
        if key in self.permissions:
            del self.permissions[key]
            self._save_json("permissions", self.permissions)
            return True
        return False
    
    async def get_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user."""
        permissions = []
        for key, data in self.permissions.items():
            if data.get("user_id") == user_id:
                permissions.append(Permission(**data))
        return permissions
    
    # ================================================================
    # Trust Relationships
    # ================================================================
    
    async def add_trusted_entity(
        self,
        user_id: int,
        entity_type: str,
        entity_id: str,
        trust_level: float = 0.5,
        reason: Optional[str] = None
    ) -> TrustedEntity:
        """Add a trusted entity."""
        entity = TrustedEntity(
            id=f"trust_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            trust_level=trust_level,
            reason=reason,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if entity.id not in self.trusted:
            self.trusted[entity.id] = {}
        self.trusted[entity.id][str(user_id)] = entity.dict()
        self._save_json("trusted", self.trusted)
        
        logger.info(f"Added trusted entity {entity_type}:{entity_id} for user {user_id}")
        return entity
    
    async def get_trusted_entities(self, user_id: int) -> List[TrustedEntity]:
        """Get all trusted entities for a user."""
        entities = []
        for entity_id, user_entities in self.trusted.items():
            if str(user_id) in user_entities:
                entities.append(TrustedEntity(**user_entities[str(user_id)]))
        return entities
    
    async def is_trusted(self, user_id: int, entity_type: str, entity_id: str) -> bool:
        """Check if an entity is trusted."""
        entities = await self.get_trusted_entities(user_id)
        for entity in entities:
            if entity.entity_type == entity_type and entity.entity_id == entity_id:
                return entity.trust_level > 0.5
        return False
    
    # ================================================================
    # Multi-Device Sync
    # ================================================================
    
    async def get_sync_state(self, user_id: int, device_id: str) -> Optional[SyncState]:
        """Get sync state for a device."""
        key = f"{user_id}:{device_id}"
        state_data = self.sync_states.get(key)
        if state_data:
            return SyncState(**state_data)
        return None
    
    async def update_sync_state(
        self,
        user_id: int,
        device_id: str,
        **kwargs
    ) -> SyncState:
        """Update sync state for a device."""
        key = f"{user_id}:{device_id}"
        
        state = await self.get_sync_state(user_id, device_id)
        if not state:
            state = SyncState(
                user_id=user_id,
                device_id=device_id,
                last_sync_at=datetime.now(),
                sync_version="1.0.0"
            )
        
        for k, v in kwargs.items():
            if hasattr(state, k):
                setattr(state, k, v)
        
        state.last_sync_at = datetime.now()
        self.sync_states[key] = state.dict()
        self._save_json("sync_states", self.sync_states)
        
        return state
    
    async def sync_context(
        self,
        user_id: int,
        from_device: str,
        to_device: str
    ) -> Dict[str, Any]:
        """Sync context between devices."""
        # This would integrate with the memory system
        # For now, return sync status
        return {
            "user_id": user_id,
            "from_device": from_device,
            "to_device": to_device,
            "synced_at": datetime.now().isoformat(),
            "status": "success"
        }
    
    # ================================================================
    # Statistics
    # ================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get identity layer statistics."""
        return {
            "total_users": len(self.profiles),
            "total_devices": sum(len(devices) for devices in self.devices.values()),
            "total_permissions": len(self.permissions),
            "total_trusted": sum(len(entities) for entities in self.trusted.values()),
            "total_sync_states": len(self.sync_states)
        }
