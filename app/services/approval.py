import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from app.models import PendingAction

logger = logging.getLogger(__name__)

class ApprovalService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_request(self, agent_type: str, query: str, data: Dict[str, Any], vap_hash: Optional[str] = None) -> int:
        """Register a new action requiring Human-In-The-Loop approval."""
        async with self.session_factory() as db:
            request = PendingAction(
                agent_type=agent_type,
                query=query,
                options=json.dumps(data),
                status="pending",
                vap_hash=vap_hash,
                created_at=datetime.now(timezone.utc)
            )
            db.add(request)
            await db.commit()
            await db.refresh(request)
            return request.id

    async def resolve_request(self, action_id: int, status: str) -> bool:
        """Approve or Deny a request."""
        if status not in ["approved", "rejected"]:
            return False
            
        async with self.session_factory() as db:
            stmt = select(PendingAction).where(PendingAction.id == action_id)
            action = (await db.execute(stmt)).scalars().first()
            
            if not action or action.status != "pending":
                return False
                
            action.status = status
            action.resolved_at = datetime.now(timezone.utc)
            await db.commit()
            return True

    async def get_pending(self) -> List[PendingAction]:
        """Fetch all currently open interventions."""
        async with self.session_factory() as db:
            stmt = select(PendingAction).where(PendingAction.status == "pending")
            results = await db.execute(stmt)
            return results.scalars().all()