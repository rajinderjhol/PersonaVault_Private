import logging
from datetime import datetime
from sqlalchemy.future import select
from app.models import PendingAction

logger = logging.getLogger(__name__)

class HITLService:
    """
    Human-In-The-Loop (HITL) Service (Phase 1.2).
    Handles the creation, approval, and denial of AI actions that require human oversight.
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    async def create_approval_request(self, action: dict, context: dict) -> dict:
        """Create a new HITL approval request."""
        async with self.session_factory() as db:
            request = PendingAction(
                action_type=action["type"],
                action_data=action,
                context=context,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(request)
            await db.commit()
            await db.refresh(request)
            
            # Send notification (e.g., via WebSocket to Admin Dashboard)
            await self.notify_approvers(request)
            
            return {
                "id": request.id,
                "status": "pending",
                "created_at": request.created_at
            }
    
    async def approve(self, action_id: int, approver_id: int) -> dict:
        """Approve a pending action."""
        async with self.session_factory() as db:
            request = await db.get(PendingAction, action_id)
            if not request:
                return {"error": "Action not found"}
            
            request.status = "approved"
            request.approved_by = approver_id
            request.approved_at = datetime.utcnow()
            await db.commit()
            
            return {
                "id": request.id,
                "status": "approved",
                "approved_by": approver_id
            }
    
    async def deny(self, action_id: int, approver_id: int, reason: str = None) -> dict:
        """Deny a pending action."""
        async with self.session_factory() as db:
            request = await db.get(PendingAction, action_id)
            if not request:
                return {"error": "Action not found"}
            
            request.status = "denied"
            request.approved_by = approver_id
            request.approved_at = datetime.utcnow()
            request.denial_reason = reason
            await db.commit()
            
            return {
                "id": request.id,
                "status": "denied",
                "reason": reason
            }

    async def notify_approvers(self, request):
        """Placeholder for approval notifications to UI."""
        logger.info(f"HITL Notification: Action {request.id} ({request.action_type}) is pending approval.")