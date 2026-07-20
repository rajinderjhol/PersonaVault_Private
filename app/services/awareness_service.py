import logging
from datetime import datetime
from app.models import PersonalContext, IoTData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

class AwarenessService:
    """
    Module responsible for the AI's contextual awareness, 
    including time, user state, and environmental factors.
    """
    @staticmethod
    async def get_contextual_awareness(user_id: int, db: AsyncSession):
        """Retrieves user situational context for grounded AI responses."""
        context_types = ['location', 'activity', 'mood', 'environment']
        awareness = {"timestamp": datetime.utcnow().isoformat()}
        
        for ctx_type in context_types:
            stmt = select(PersonalContext).where(
                PersonalContext.user_id == user_id, 
                PersonalContext.context_type == ctx_type
            ).order_by(PersonalContext.timestamp.desc())
            res = await db.execute(stmt)
            latest = res.scalars().first()
            if latest:
                awareness[ctx_type] = latest.value
        
        return awareness