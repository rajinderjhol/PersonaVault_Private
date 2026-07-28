from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import random

router = APIRouter(prefix="/api/v1/timeline/trends", tags=["trends"])

@router.get("/incident_response")
async def mock_incident_response_trends(days: int = 30):
    """Mock trends data until real endpoint is implemented."""
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
        "data": data[::-1],  # Reverse to show oldest first
        "days": days,
        "total": sum(d["count"] for d in data)
    }
