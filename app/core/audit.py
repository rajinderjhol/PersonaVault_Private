from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog
import logging
import json

logger = logging.getLogger(__name__)

async def audit_middleware(request: Request, call_next):
    """
    Middleware to log state-changing requests for compliance and security.
    """
    # Process the request first
    response: Response = await call_next(request)
    
    # Only audit state-changing operations
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        db: AsyncSession = getattr(request.state, "db", None)
        user = getattr(request.state, "user", None)
        
        if db:
            try:
                # Extract path details
                path_parts = request.url.path.strip("/").split("/")
                resource_type = path_parts[-2] if len(path_parts) > 1 else "root"
                
                # Create the audit entry
                log_entry = AuditLog(
                    user_id=user.id if user else None,
                    action=f"{request.method}_{request.url.path}",
                    resource_type=resource_type,
                    resource_id=None, # Identification logic for IDs could be added here
                    details=json.dumps({
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "client_host": request.client.host if request.client else "unknown"
                    }),
                    ip_address=request.client.host if request.client else None
                )
                db.add(log_entry)
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to record audit log: {e}")
                # We don't fail the request if auditing fails, but we log the error

    return response