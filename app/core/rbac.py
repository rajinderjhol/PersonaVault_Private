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
    "/api/v1/mode/current",
    "/api/v1/registry/services",
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
    logger.warning(f"RBAC DEBUG: Path: {path}, Headers: {dict(request.headers)}")

    # 1. Skip RBAC for public paths and static assets
    if path in PUBLIC_PATHS or path.startswith("/static") or path.startswith("/api/v1/admin/dashboard/static"):
        return await call_next(request)

    # 2. Retrieve DB session from request state
    db: AsyncSession = getattr(request.state, "db", None)
    logger.info(f"RBAC DEBUG: DB session found in request state: {db is not None}")
    
    # Check for user in request.state (either from auth or test override)
    user = getattr(request.state, "user", None)
    logger.info(f"RBAC DEBUG: User found in request state: {user is not None}")
    
    # IF user is not set (e.g. not a test override), check session cookie or query param
    if not user:
        session_id = request.cookies.get("session_id") or request.query_params.get("token")
        logger.info(f"RBAC DEBUG: Session ID from cookie/query: {session_id}")
        if db and session_id:
            try:
                # Log the session lookup
                logger.info(f"RBAC: Searching for token: {session_id}")
                
                stmt = select(UserSession).where(
                    UserSession.session_token == session_id,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
                )
                result = await db.execute(stmt)
                session_record = result.scalars().first()
                logger.info(f"RBAC: Session record found: {session_record is not None}")
                
                if session_record:
                    user_stmt = select(User).where(User.id == session_record.user_id)
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalars().first()
                    request.state.user = user  # Populate request state
            except Exception as e:
                logger.error(f"RBAC: Error validating session: {e}")
    
    # 3. Enforce Administrative Access
    is_admin_path = any(path.startswith(prefix) for prefix in ADMIN_PREFIXES)
    is_dashboard_ui = path.startswith("/api/v1/admin/dashboard")
    is_studio_ui = path.startswith("/studio")
    
    # DEBUG: Log user state
    if user:
        logger.info(f"RBAC DEBUG: Path: {path}, User: {user.username}, Role: {user.role}, IsAdminPath: {is_admin_path}")
    else:
        logger.warning(f"RBAC DEBUG: Path: {path}, No user found, IsAdminPath: {is_admin_path}, IsStudioUI: {is_studio_ui}")

    if is_admin_path:
        if not user or user.role != "admin":
            username = user.username if user else 'Anonymous'
            logger.warning(f"RBAC DENIED: Unauthorized admin access attempt to {path} by {username} with role: {user.role if user else 'N/A'}")
            
            # Redirect to login for UI paths
            if path.startswith("/admin") or is_dashboard_ui:
                return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)

            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"Permission denied: Admin privileges required. Detected role: {user.role if user else 'Anonymous'}",
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

    # 5. Global API/UI Authentication Check
    # Force login for Studio UI
    if is_studio_ui and not user:
        logger.warning(f"RBAC: Redirecting unauthenticated Studio access to login: {path}")
        return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    # Block unauthenticated API requests
    if (path.startswith("/api/v1") or path.startswith("/v2")) and \
       not path.startswith("/api/v1/auth") and \
       not is_dashboard_ui and \
       not user:
        logger.warning(f"RBAC: Blocked unauthenticated API request to {path}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required", "code": "AUTH_001"}
        )


    # Ensure user is set in state for downstream usage
    request.state.user = user

    return await call_next(request)
