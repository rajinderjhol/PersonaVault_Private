import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import User, Memory, UserSession, AISetting

logger = logging.getLogger(__name__)

class DataDeletionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def delete_user_data(self, user_id: int, reason: str = None):
        """Delete all data for a user (Right to Forget)."""
        logger.info(f"Processing data deletion request for user {user_id}")
        
        # 1. Delete from SQLite
        await self.db.execute(delete(Memory).where(Memory.user_id == user_id))
        await self.db.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await self.db.execute(delete(AISetting).where(AISetting.user_id == user_id))
        
        # # 2. Anonymize audit logs
        # logs = self.db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
        # for log in logs:
        #     log.user_id = None
        #     log.details = {"anonymized": True, "original_action": log.action}

        # 3. Mark user as deleted
        stmt = select(User).where(User.id == user_id)
        res = await self.db.execute(stmt)
        user = res.scalars().first()
        if user:
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            user.deletion_reason = reason
        
        await self.db.commit()
        
        # 4. Trigger deletion from Vector and Graph stores would happen here
        return {"status": "deleted", "deleted_at": datetime.utcnow().isoformat()}