"""
MCP Device Connector - Connect and control devices
"""
from typing import Dict, Any, List, Optional
import logging

from app.mcp.base import BaseMCPConnector
from app.mcp.device_registry import DeviceRegistry, DeviceType, DeviceStatus, DeviceTrustLevel, DeviceCapability

logger = logging.getLogger(__name__)


class DeviceConnector(BaseMCPConnector):
    """MCP connector for device operations."""
    
    def __init__(self, config: Dict[str, Any], db_session):
        super().__init__(config)
        self.registry = DeviceRegistry(db_session)
    
    async def register_new_device(
        self,
        device_type: str,
        device_name: str,
        capabilities: List[str],
        config: Dict[str, Any],
        user_id: str,
        trust_level: str = "medium"
    ) -> Dict:
        """Register a new device."""
        trust_level_map = {
            "full": DeviceTrustLevel.FULL,
            "high": DeviceTrustLevel.HIGH,
            "medium": DeviceTrustLevel.MEDIUM,
            "low": DeviceTrustLevel.LOW,
            "untrusted": DeviceTrustLevel.UNTRUSTED
        }
        
        return await self.registry.register_device(
            device_type=DeviceType(device_type.lower()),
            device_name=device_name,
            capabilities=[DeviceCapability(c) for c in capabilities],
            config=config,
            user_id=user_id,
            trust_level=trust_level_map.get(trust_level.lower(), DeviceTrustLevel.MEDIUM)
        )
    
    async def list_devices(self, user_id: str) -> List[Dict]:
        """List all devices for a user."""
        return await self.registry.get_user_devices(user_id)
    
    async def control_device(self, device_id: str, action: str, params: Dict) -> Dict:
        """Send a control command to a device."""
        return await self.registry.execute_device_action(device_id, action, params)
    
    async def get_device_status(self, device_id: str) -> Dict:
        """Get device status."""
        device = await self.registry.get_device(device_id)
        if device:
            # Update last_seen
            await self.registry.update_device_status(device_id, DeviceStatus.ONLINE)
            return device
        return {"error": "Device not found"}
    
    async def set_trust_level(self, device_id: str, trust_level: str) -> Dict:
        """Set device trust level."""
        trust_level_map = {
            "full": DeviceTrustLevel.FULL,
            "high": DeviceTrustLevel.HIGH,
            "medium": DeviceTrustLevel.MEDIUM,
            "low": DeviceTrustLevel.LOW,
            "untrusted": DeviceTrustLevel.UNTRUSTED
        }
        level = trust_level_map.get(trust_level.lower(), DeviceTrustLevel.MEDIUM)
        return await self.registry.update_trust_level(device_id, level)
    
    async def get_telemetry(self, device_id: str, time_range: str = "1h") -> Dict:
        """Get device telemetry."""
        return await self.registry.get_device_telemetry(device_id, time_range)
    
    async def revoke_device(self, device_id: str) -> Dict:
        """Revoke a device."""
        return await self.registry.revoke_device(device_id)
