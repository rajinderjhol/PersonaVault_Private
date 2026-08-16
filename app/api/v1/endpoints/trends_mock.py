from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import random

router = APIRouter(prefix="/timeline/trends", tags=["trends"])

@router.get("/{domain}")
async def mock_trends(domain: str, days: int = 30):
    """Mock trends data for a given domain."""
    data = []
    now = datetime.now(timezone.utc)
    for i in range(days):
        date = now - timedelta(days=i)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": random.randint(0, 10)
        })
    return {
        "status": "success",
        "domain": domain,
        "data": data[::-1],
        "days": days,
        "total": sum(d["count"] for d in data)
    }
