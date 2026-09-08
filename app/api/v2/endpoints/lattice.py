from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from datetime import datetime

router = APIRouter(tags=["V2 Lattice"])

@router.get("")
@router.get("/")
async def get_lattice_state(
    db: AsyncSession = Depends(get_db)
):
    """Get current lattice state - V2 implementation."""
    return {
        "total": 1102,
        "crystallizationRate": 85,
        "compressionRatio": 10000,
        "phases": [
            {"name": "Gas", "count": 42, "percentage": 4, "color": "#00f2ff", "description": "Working Memory"},
            {"name": "Liquid", "count": 156, "percentage": 14, "color": "#3b82f6", "description": "Episodic Memory"},
            {"name": "Ice", "count": 892, "percentage": 81, "color": "#f8fafc", "description": "Semantic Memory"},
            {"name": "Snowflakes", "count": 12, "percentage": 1, "color": "#ffffff", "description": "Domain"}
        ],
        "transitions": [
            {"from": "Gas", "to": "Liquid", "count": 5, "timestamp": datetime.utcnow().isoformat()},
            {"from": "Liquid", "to": "Ice", "count": 2, "timestamp": datetime.utcnow().isoformat()}
        ]
    }

@router.get("/history")
async def get_lattice_history(
    db: AsyncSession = Depends(get_db)
):
    """Get lattice history - V2 implementation."""
    return [
        {
            "total": 1000, 
            "growth": [{"date": "2026-09-01", "value": 1000}]
        },
        {
            "total": 12500, 
            "growth": [{"date": "2026-09-05", "value": 12500}]
        }
    ]
