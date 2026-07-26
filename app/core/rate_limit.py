import time
import logging
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.config import Config

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Service for managing rate limits using Redis with an in-memory fallback.
    """
    def __init__(self):
        self.redis_url = getattr(Config, "REDIS_URL", None)
        self.window = getattr(Config, "RATE_LIMIT_WINDOW", 60)
        self.max_requests = getattr(Config, "MAX_REQUESTS_PER_WINDOW", 100)
        self.redis = None
        
        if self.redis_url:
            try:
                import redis
                self.redis = redis.from_url(self.redis_url)
                logger.info("RateLimiter: Established connection to Redis backend.")
            except ImportError:
                logger.warning("redis-py not installed. Falling back to in-memory store.")
            except Exception as e:
                logger.error(f"RateLimiter: Could not connect to Redis: {e}")
        
        if not self.redis:
            self.store = defaultdict(list)
            logger.warning("RateLimiter: Using in-memory store (unsuitable for production).")

    async def is_rate_limited(self, client_ip: str) -> bool:
        """
        Checks if the request count for a given IP has exceeded the window threshold.
        """
        if self.redis:
            try:
                key = f"rate_limit:{client_ip}"
                # Check current count before incrementing to save on pipeline overhead if already limited
                current = self.redis.get(key)
                if current and int(current) >= self.max_requests:
                    return True
                
                # Atomic increment and expiration
                pipe = self.redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window)
                pipe.execute()
                return False
            except Exception as e:
                logger.error(f"Redis rate limit lookup failed: {e}")
                return False # Fail open to prevent blocking legitimate traffic during outages

        # In-memory sliding window implementation
        now = time.time()
        self.store[client_ip] = [
            t for t in self.store[client_ip] 
            if now - t < self.window
        ]
        
        if len(self.store[client_ip]) >= self.max_requests:
            return True
        
        self.store[client_ip].append(now)
        return False

# Global instance to be used by middleware
limiter = RateLimiter()

async def rate_limiter(request: Request, call_next):
    """
    FastAPI middleware for IP-based rate limiting.
    """
    if request.url.path in ["/health", "/metrics", "/health/liveness", "/health/readiness"]:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    if await limiter.is_rate_limited(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many requests. Please try again later.", 
                "retry_after": limiter.window
            }
        )

    return await call_next(request)