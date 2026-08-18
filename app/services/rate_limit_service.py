
import httpx
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RateLimitCache:
    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {}

    def update(self, provider: str, headers: Dict[str, str]):
        self.limits[provider.lower()] = {
            "remaining_requests": headers.get("x-ratelimit-remaining-requests"),
            "remaining_tokens": headers.get("x-ratelimit-remaining-tokens"),
            "reset_requests": headers.get("x-ratelimit-reset-requests"),
            "reset_tokens": headers.get("x-ratelimit-reset-tokens"),
            "last_updated": httpx.Any # Actually want timestamp
        }

    def get(self, provider: str) -> Optional[Dict[str, Any]]:
        return self.limits.get(provider.lower())

class RateLimitService:
    # ... existing ADAPTERS ...
    ADAPTERS = {
        "groq": {
            "type": "headers",
            "mapping": {
                "remaining_requests": "x-ratelimit-remaining-requests",
                "remaining_tokens": "x-ratelimit-remaining-tokens",
                "reset_requests": "x-ratelimit-reset-requests",
                "reset_tokens": "x-ratelimit-reset-tokens"
            },
            "url": "https://api.groq.com/openai/v1/models"
        }
    }

    def __init__(self):
        self.cache = RateLimitCache()

    async def get_stats(self, provider: str) -> Dict[str, Any]:
        config = self.ADAPTERS.get(provider.lower())
        if not config:
            return {"error": f"Provider {provider} not supported for rate limiting"}
        
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key:
            return {"error": f"{provider.upper()}_API_KEY not configured"}
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(config["url"], headers=headers)
                
                if response.status_code == 200:
                    self.cache.update(provider, response.headers)
                    return {**self.cache.get(provider), "status": "connected"}
                else:
                    return {"error": f"API returned {response.status_code}", "status": "error"}
                
        except Exception as e:
            logger.error(f"Failed to fetch {provider} rate limits: {e}")
            return {"error": str(e)}

# Global instance
rate_limit_service = RateLimitService()
