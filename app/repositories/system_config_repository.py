from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.system_config import SystemConfig
from typing import Dict, Any, Optional

class SystemConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalars().first()
        return config.value if config else None

    async def save_config(self, key: str, value: Dict[str, Any]):
        result = await self.db.execute(select(SystemConfig).where(SystemConfig.key == key))
        config = result.scalars().first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            self.db.add(config)
        await self.db.commit()
