"""
Async Audit Service for async operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

class AsyncAuditService:
    """Async version of AuditService."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_decision(self, event):
        """Log a decision asynchronously."""
        audit_id = f"audit-{event.id}-{datetime.now(timezone.utc).timestamp()}"
        return audit_id
    
    async def log_action(self, user_id, action, resource, resource_id):
        """Log an action asynchronously."""
        audit_id = f"audit-{resource_id}-{datetime.now(timezone.utc).timestamp()}"
        return audit_id
