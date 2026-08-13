from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_config import SystemConfig
import json

class SystemConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self, key: str) -> Optional[Any]:
        """Get a configuration value by key."""
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalars().first()
        if config is None:
            return None
        value = config.value
        # Try to parse JSON if it's a string
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def save_config(self, key: str, value: Any):
        """Save a configuration value."""
        # Convert to JSON string if it's not a string
        if not isinstance(value, str):
            value = json.dumps(value)
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalars().first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            self.db.add(config)
        await self.db.commit()
