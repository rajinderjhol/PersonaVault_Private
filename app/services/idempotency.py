"""
Idempotency Service for Durable Execution.
Ensures actions are only executed once, even with retries.
"""
import logging
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import Base
from sqlalchemy import Column, String, DateTime, JSON

logger = logging.getLogger(__name__)

# Define model inline to avoid import issues
class IdempotentAction(Base):
    __tablename__ = "idempotent_actions"
    
    id = Column(String, primary_key=True, index=True)  # idempotency key
    action_type = Column(String, index=True)
    state = Column(JSON, default={})
    result = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

class IdempotencyService:
    """Ensure actions are only executed once."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def execute_once(self, key: str, action_type: str, action_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute an action only once using idempotency key.
        
        Args:
            key: Unique idempotency key (e.g., f"{event_id}_{action_type}")
            action_type: Type of action being performed
            action_func: Async function to execute
            *args, **kwargs: Arguments to pass to action_func
        
        Returns:
            Dict with result and idempotent status
        """
        async with self.session_factory() as db:
            # Check if already executed
            stmt = select(IdempotentAction).where(IdempotentAction.id == key)
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                if existing.status == "completed":
                    logger.info(f"✅ Idempotent action {key} already completed")
                    return {"idempotent": True, "result": existing.result}
                elif existing.status == "pending":
                    logger.info(f"⏳ Idempotent action {key} already in progress")
                    return {"idempotent": True, "status": "pending", "message": "Action already in progress"}
                elif existing.status == "failed":
                    # Allow retry of failed actions
                    logger.info(f"🔄 Retrying failed idempotent action {key}")
                    # Delete failed record to allow retry
                    await db.delete(existing)
                    await db.commit()
            
            # Create record
            action = IdempotentAction(
                id=key,
                action_type=action_type,
                status="pending"
            )
            db.add(action)
            await db.commit()
            await db.refresh(action)
            
            try:
                # Execute action
                logger.info(f"▶️ Executing idempotent action {key}")
                result = await action_func(*args, **kwargs)
                
                # Update record
                action.status = "completed"
                action.result = result
                action.completed_at = datetime.now(timezone.utc)
                await db.commit()
                
                logger.info(f"✅ Idempotent action {key} completed")
                return {"idempotent": False, "result": result}
                
            except Exception as e:
                logger.error(f"❌ Idempotent action {key} failed: {e}")
                action.status = "failed"
                action.result = {"error": str(e)}
                await db.commit()
                raise
    
    async def get_action_status(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the status of an idempotent action."""
        async with self.session_factory() as db:
            stmt = select(IdempotentAction).where(IdempotentAction.id == key)
            result = await db.execute(stmt)
            action = result.scalars().first()
            
            if not action:
                return None
            
            return {
                "id": action.id,
                "action_type": action.action_type,
                "status": action.status,
                "result": action.result,
                "created_at": action.created_at.isoformat(),
                "completed_at": action.completed_at.isoformat() if action.completed_at else None
            }
