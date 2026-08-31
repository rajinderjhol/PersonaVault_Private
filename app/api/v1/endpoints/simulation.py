from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.policy_simulator_service import PolicySimulatorService
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

class SimulationRequest(BaseModel):
    domain: str
    params: Dict[str, Any]
    start_date: datetime
    end_date: datetime

@router.post("/policy")
async def run_policy_simulation(
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    service = PolicySimulatorService(db)
    result = await service.simulate_policy_impact(
        domain=request.domain,
        params=request.params,
        start_date=request.start_date,
        end_date=request.end_date
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
