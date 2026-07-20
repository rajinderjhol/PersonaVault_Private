from typing import Dict, Any
from datetime import datetime
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import IoTData, MedicalAlert, IoTDevice
import logging

logger = logging.getLogger(__name__)

class IoTService:
    @staticmethod
    async def process_realtime_data(data: Dict[str, Any]):
        """Process real-time IoT data from WebSocket"""
        device_id = data.get("device_id")
        data_type = data.get("type")
        value = data.get("value")
        user_id = data.get("user_id")
        
        async with SessionLocal() as db:
            try:
                # Store the incoming data stream
                iot_data = IoTData(
                    device_id=device_id,
                    user_id=user_id,
                    data_type=data_type,
                    value=value,
                    timestamp=datetime.utcnow()
                )
                db.add(iot_data)
                
                # Check for immediate health alerts based on thresholds
                await IoTService.check_health_alerts(user_id, data_type, value, db)
                
                # Update device last sync metadata
                stmt = select(IoTDevice).where(IoTDevice.id == device_id)
                result = await db.execute(stmt)
                device = result.scalars().first()
                if device:
                    device.last_sync = datetime.utcnow()
                
                await db.commit() # Already async-safe with your SessionLocal
            except Exception as e:
                logger.error(f"Failed to process IoT data: {e}")
                await db.rollback()
    
    @staticmethod
    async def check_health_alerts(user_id: int, data_type: str, value: Any, db):
        """Logic for triggering medical alerts based on personal health data."""
        # Thresholds can be moved to a configuration file or per-user settings
        thresholds = {
            "heart_rate": {"min": 40, "max": 120},
            "blood_pressure_systolic": {"min": 90, "max": 140},
            "blood_pressure_diastolic": {"min": 60, "max": 90},
            "glucose": {"min": 70, "max": 140},
            "temperature": {"min": 36.0, "max": 38.0}
        }
        
        if data_type in thresholds:
            threshold = thresholds[data_type]
            alert_type = None
            severity = "low"
            message = ""
            
            # Validate numeric value for threshold comparison
            if isinstance(value, (int, float)):
                if value < threshold["min"]:
                    alert_type = f"low_{data_type}"
                    severity = "medium"
                    message = f"Low {data_type} detected: {value}"
                elif value > threshold["max"]:
                    alert_type = f"high_{data_type}"
                    severity = "high"
                    message = f"High {data_type} detected: {value}"
            
            if alert_type:
                alert = MedicalAlert(
                    user_id=user_id,
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    data={"value": value, "threshold": threshold},
                    created_at=datetime.utcnow()
                )
                db.add(alert)
                logger.warning(f"Health alert generated: {alert_type} for user {user_id}")