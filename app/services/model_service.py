from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import SystemConfig
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, db: AsyncSession, ai_client):
        self.db = db
        self.ai_client = ai_client

    async def list_models(self):
        """List installed Ollama models and identify the active one from DB."""
        active_model = "tinydolphin"
        try:
            stmt = select(SystemConfig).where(SystemConfig.key == "ai_provider_ollama_model")
            result = await self.db.execute(stmt)
            config = result.scalars().first()
            if config:
                active_model = config.value
            
            # Using the injected ai_client
            res = await self.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
            data = res.json()
            return {
                "models": data.get("models", []),
                "active_model": active_model
            }
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return {"models": [], "active_model": active_model}
