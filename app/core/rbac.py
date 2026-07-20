from fastapi import Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserSession
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# List of paths that are exempt from RBAC checks
PUBLIC_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/health/liveness",
    "/health/readiness",
    "/metrics",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/favicon.ico"
}

# Prefixes for routes requiring administrative privileges
ADMIN_PREFIXES = ["/api/v1/admin", "/admin"]

async def rbac_middleware(request: Request, call_next):
    """
    Middleware to enforce Role-Based Access Control (RBAC).
    
    Validates user sessions via cookies and enforces role-based constraints 
    on administrative and protected API routes.
    """
    path = request.url.path
    
    # 1. Skip RBAC for public paths and static assets
    if path in PUBLIC_PATHS or path.startswith("/static"):
        return await call_next(request)

    # 2. Retrieve DB session from request state
    # This relies on db_session_middleware being the outermost layer in main.py
    db: AsyncSession = getattr(request.state, "db", None)
    
    # 2.1 Check if user was already identified by upstream middleware (e.g. session_auth_middleware)
    user = getattr(request.state, "user", None)
    session_id = request.cookies.get("session_id")
    
    if not user and db and session_id:
        try:
            # Look up active session
            stmt = select(UserSession).where(
                UserSession.session_token == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
            result = await db.execute(stmt)
            session_record = result.scalars().first()
            
            if session_record:
                user_stmt = select(User).where(User.id == session_record.user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalars().first()
        except Exception as e:
            logger.error(f"RBAC: Error validating session: {e}")

    # 3. Enforce Administrative Access
    is_admin_path = any(path.startswith(prefix) for prefix in ADMIN_PREFIXES)
    if is_admin_path:
        if not user or user.role != "admin":
            logger.warning(f"RBAC DENIED: Unauthorized admin access attempt to {path} by {user.username if user else 'Anonymous'}")
            
            # If it's a UI path (not an API path), redirect to login
            if path.startswith("/admin") and not path.startswith("/api"):
                return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Permission denied: Admin privileges required",
                    "code": "PERM_001"
                }
            )

    # 4. Global API Authentication Check
    # Protect all /api/v1 routes except authentication endpoints
    if path.startswith("/api/v1") and not path.startswith("/api/v1/auth") and not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required", "code": "AUTH_001"}
        )

    # 5. Future Scope Checks (Roadmap Milestone)
    # Granular checks based on user.permissions can be implemented here.

    # Store identified user in request state for downstream handler use
    request.state.user = user

    return await call_next(request)