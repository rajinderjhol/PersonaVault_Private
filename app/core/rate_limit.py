from fastapi import Request, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import logging
from app.config import Config

logger = logging.getLogger(__name__)

# In-memory store for rates: {ip: [timestamps]}
# NOTE: Replace with Redis for multi-process / Kubernetes deployments (Phase 3)
_rate_limit_store = defaultdict(list)

# Configuration is now driven by environment variables via Config
RATE_LIMIT_WINDOW = Config.RATE_LIMIT_WINDOW
MAX_REQUESTS_PER_WINDOW = Config.MAX_REQUESTS_PER_WINDOW

# Paths that are always exempt from rate limiting
_EXEMPT_PATHS = {
    "/health",
    "/health/liveness",
    "/health/readiness",
    "/health/engine",
}

async def rate_limiter(request: Request, call_next):
    """
    Sliding window rate limiter based on client IP.
    Configuration is driven by RATE_LIMIT_WINDOW and MAX_REQUESTS_PER_WINDOW env vars.
    NOTE: For distributed (K8s) deployments, migrate to Redis-backed rate limiting.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Skip rate limiting for health checks
    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    # Skip rate limiting for static assets
    if request.url.path.startswith("/api/v1/admin/dashboard/static/"):
        return await call_next(request)

    # Clean up old timestamps outside the window
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning(f"Rate limit exceeded for IP: {client_ip} on {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests. Please try again later.",
                "retry_after": RATE_LIMIT_WINDOW,
                "code": "RATE_001",
            },
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    _rate_limit_store[client_ip].append(now)
    return await call_next(request)
