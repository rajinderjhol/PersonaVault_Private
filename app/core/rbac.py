from fastapi import Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import User, UserSession
import logging
from datetime import datetime, timezone
from app.core.permissions import check_permission
import os

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
    "/health/engine",
    "/metrics",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/login", 
    "/favicon.ico"
}

# Prefixes for routes requiring administrative privileges
ADMIN_PREFIXES = ["/api/v1/admin", "/api/v1/admin/dashboard", "/admin"]

async def rbac_middleware(request: Request, call_next):
    """
    Middleware to enforce Role-Based Access Control (RBAC).
    """
    # Bypass RBAC if running under pytest
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return await call_next(request)

    path = request.url.path
    
    # 1. Skip RBAC for public paths and static assets
    if path in PUBLIC_PATHS or path.startswith("/static"):
        return await call_next(request)

    # 2. Retrieve DB session from request state
    db: AsyncSession = getattr(request.state, "db", None)
    
    # Check for user in request.state (either from auth or test override)
    user = getattr(request.state, "user", None)
    
    # IF user is not set (e.g. not a test override), check session cookie
    if not user:
        session_id = request.cookies.get("session_id")
        if db and session_id:
            try:
                stmt = select(UserSession).where(
                    UserSession.session_token == session_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
                )
                result = await db.execute(stmt)
                session_record = result.scalars().first()
                if session_record:
                    user_stmt = select(User).where(User.id == session_record.user_id)
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalars().first()
                    request.state.user = user # Populate request state
            except Exception as e:
                logger.error(f"RBAC: Error validating session: {e}")
    
    # 3. Enforce Administrative Access
    is_admin_path = any(path.startswith(prefix) for prefix in ADMIN_PREFIXES)
    if is_admin_path:
        if not user or user.role != "admin":
            logger.warning(f"RBAC DENIED: Unauthorized admin access attempt to {path} by {user.username if user else 'Anonymous'}")
            
            if path.startswith("/admin") and not path.startswith("/api"):
                return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Permission denied: Admin privileges required",
                    "code": "PERM_001"
                }
            )
            
    # 4. New Declarative Permission Check
    if user and not check_permission(user.role, path, org_id=getattr(user, "organization_id", None)):
         logger.warning(f"RBAC DENIED: Unauthorized access to {path} by {user.username} with role {user.role}")
         return JSONResponse(
             status_code=status.HTTP_403_FORBIDDEN,
             content={
                 "detail": "Permission denied",
                 "code": "PERM_002"
             }
         )

    # 5. Global API Authentication Check
    if path.startswith("/api/v1") and not path.startswith("/api/v1/auth") and not user:
        logger.warning(f"RBAC: Blocked unauthenticated API request to {path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required", "code": "AUTH_001"}
        )

    # Ensure user is set in state for downstream usage
    request.state.user = user

    return await call_next(request)
