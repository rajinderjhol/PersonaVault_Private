"""
Unified Device Registry - Manage all devices (IoT, Medical, Enterprise, Camera, etc.)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.device import Device
from app.mcp.device_types import DeviceType, DeviceCapability, DeviceStatus, DeviceTrustLevel

logger = logging.getLogger(__name__)

class DeviceRegistry:
    """Unified device registry with trust management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_device(
        self,
        device_type: DeviceType,
        device_name: str,
        capabilities: List[DeviceCapability],
        config: Dict[str, Any],
        user_id: str,
        trust_level: DeviceTrustLevel = DeviceTrustLevel.MEDIUM,
        metadata: Dict[str, Any] = None
    ) -> Dict:
        """Register a new device."""
        device = Device(
            id=str(uuid4()),
            device_type=device_type,
            device_name=device_name,
            capabilities=capabilities,
            config=config,
            user_id=user_id,
            trust_level=trust_level,
            status=DeviceStatus.PENDING,
            device_metadata=metadata or {},
            registered_at=datetime.utcnow()
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        
        # Log registration
        logger.info(f"Device registered: {device_name} ({device_type}) for user {user_id}")
        
        return device.to_dict()
    
    async def get_device(self, device_id: str) -> Optional[Dict]:
        """Get device by ID."""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        return device.to_dict() if device else None
    
    async def get_user_devices(self, user_id: str) -> List[Dict]:
        """Get all devices for a user."""
        result = await self.db.execute(
            select(Device).where(Device.user_id == user_id)
        )
        devices = result.scalars().all()
        return [d.to_dict() for d in devices]
    
    async def update_device_status(self, device_id: str, status: DeviceStatus) -> Dict:
        """Update device status."""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        if not device:
            return {"error": "Device not found"}
        
        device.status = status
        device.last_seen = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        
        return device.to_dict()
    
    async def update_trust_level(self, device_id: str, trust_level: DeviceTrustLevel) -> Dict:
        """Update device trust level."""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        if not device:
            return {"error": "Device not found"}
        
        device.trust_level = trust_level
        device.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        
        return device.to_dict()
    
    async def execute_device_action(
        self,
        device_id: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict:
        """Execute an action on a device."""
        device = await self.get_device(device_id)
        if not device:
            return {"error": "Device not found"}
        
        # Route action based on device type
        device_type = device.get("device_type")
        
        if device_type == DeviceType.IOT:
            return await self._execute_iot_action(device, action, params)
        elif device_type == DeviceType.ROBOT:
            return await self._execute_robot_action(device, action, params)
        elif device_type == DeviceType.MEDICAL:
            return await self._execute_medical_action(device, action, params)
        elif device_type == DeviceType.CAMERA:
            return await self._execute_camera_action(device, action, params)
        elif device_type == DeviceType.ENTERPRISE:
            return await self._execute_enterprise_action(device, action, params)
        elif device_type == DeviceType.SMART_HOME:
            return await self._execute_smart_home_action(device, action, params)
        else:
            return {"error": f"Unsupported device type: {device_type}"}
    
    async def _execute_iot_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute IoT device action."""
        # Example: MQTT, REST, WebSocket
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "IoT action executed"
        }
    
    async def _execute_robot_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute robot device action."""
        # Example: ROS, gRPC
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "Robot action executed"
        }
    
    async def _execute_medical_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute medical device action."""
        # Example: HL7, FHIR
        if action == "get_vitals":
            return {
                "status": "success",
                "device_id": device.get("id"),
                "vitals": {
                    "heart_rate": 72,
                    "blood_pressure": "120/80",
                    "temperature": 98.6,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "Medical action executed"
        }
    
    async def _execute_camera_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute camera device action."""
        # Example: RTSP, ONVIF
        if action == "get_snapshot":
            return {
                "status": "success",
                "device_id": device.get("id"),
                "image_url": "https://camera.local/snapshot.jpg",
                "timestamp": datetime.utcnow().isoformat()
            }
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "Camera action executed"
        }
    
    async def _execute_enterprise_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute enterprise system action."""
        # Example: Salesforce, SAP, Workday
        if action == "query_data":
            return {
                "status": "success",
                "device_id": device.get("id"),
                "data": {
                    "source": device.get("config", {}).get("system", "enterprise"),
                    "query": params.get("query"),
                    "results": []
                }
            }
        if action == "create_record":
            return {
                "status": "success",
                "device_id": device.get("id"),
                "record": params.get("data", {}),
                "created_at": datetime.utcnow().isoformat()
            }
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "Enterprise action executed"
        }
    
    async def _execute_smart_home_action(self, device: Dict, action: str, params: Dict) -> Dict:
        """Execute smart home device action."""
        # Example: Google Home, Alexa, HomeKit
        return {
            "status": "success",
            "device_id": device.get("id"),
            "action": action,
            "params": params,
            "result": "Smart home action executed"
        }
    
    async def get_device_telemetry(self, device_id: str, time_range: str = "1h") -> Dict:
        """Get device telemetry data."""
        # In production, this would query time-series data
        return {
            "device_id": device_id,
            "time_range": time_range,
            "data_points": [
                {"timestamp": datetime.utcnow().isoformat(), "value": 1.0},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(), "value": 0.8},
                {"timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(), "value": 0.9}
            ]
        }
    
    async def revoke_device(self, device_id: str) -> Dict:
        """Revoke a device (permanently disable)."""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        if not device:
            return {"error": "Device not found"}
        
        device.status = DeviceStatus.OFFLINE
        device.trust_level = DeviceTrustLevel.UNTRUSTED
        device.revoked_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(device)
        
        return {"status": "success", "device_id": device_id, "revoked_at": device.revoked_at.isoformat()}
