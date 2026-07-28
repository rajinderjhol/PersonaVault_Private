from fastapi import Request, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# In-memory store for rates: {ip: [timestamps]}
_rate_limit_store = defaultdict(list)

# Configuration: 100 requests per minute
RATE_LIMIT_WINDOW = 60 
MAX_REQUESTS_PER_WINDOW = 100

async def rate_limiter(request: Request, call_next):
    """
    Simple sliding window rate limiter based on client IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Skip rate limiting for health checks and metrics
    if request.url.path in ["/health", "/metrics", "/health/liveness", "/health/readiness", "/health/engine"]:
        return await call_next(request)
    
    # Skip rate limiting for static assets
    if request.url.path.startswith("/api/v1/admin/dashboard/static/"):
        return await call_next(request)

    # Clean up old timestamps
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] 
        if now - t < RATE_LIMIT_WINDOW
    ]
    
    if len(_rate_limit_store[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please try again later.", "retry_after": RATE_LIMIT_WINDOW}
        )
    
    _rate_limit_store[client_ip].append(now)
    return await call_next(request)
