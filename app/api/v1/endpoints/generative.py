"""
Generative Decision Making API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.services.generative_decision import GenerativeDecisionMaker

router = APIRouter(prefix="/api/v1/generative", tags=["generative"])

class DecisionRequest(BaseModel):
    problem: str
    context: Optional[Dict[str, Any]] = {}

class DecisionResponse(BaseModel):
    understanding: Dict[str, Any]
    options: list
    tradeoffs: Dict[str, Any]
    recommendation: Dict[str, Any]
    timestamp: str

@router.post("/decide", response_model=DecisionResponse)
async def generate_decision(
    request: DecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate and evaluate multiple decision paths."""
    engine = GenerativeDecisionMaker(db)
    result = await engine.decide(request.problem, request.context)
    return result

@router.post("/options")
async def generate_options(
    request: DecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate multiple options without simulation."""
    engine = GenerativeDecisionMaker(db)
    understanding = await engine._understand_problem(request.problem, request.context)
    options = await engine._generate_options(understanding, request.context)
    return {"options": options}

@router.post("/simulate")
async def simulate_options(
    request: DecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simulate outcomes for given options."""
    engine = GenerativeDecisionMaker(db)
    understanding = await engine._understand_problem(request.problem, request.context)
    options = await engine._generate_options(understanding, request.context)
    simulated = await engine._simulate_outcomes(options, request.context)
    return {"simulations": simulated}
