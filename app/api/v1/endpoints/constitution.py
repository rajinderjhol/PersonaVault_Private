"""
Constitutional Editor - Governance constitution management with temperature controls
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.models import SystemConfig, User
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/constitution", tags=["constitution"])


class TemperatureControl(BaseModel):
    energy_level: float = Field(ge=0.0, le=1.0, description="Energy level for crystallization")
    vibration: float = Field(ge=0.0, le=1.0, description="Vibration rate for pattern formation")
    description: Optional[str] = None


class ConstitutionUpdate(BaseModel):
    version: Optional[str] = None
    principles: Optional[Dict[str, bool]] = None
    policies: Optional[Dict[str, Any]] = None
    temperature: Optional[TemperatureControl] = None
    rules: Optional[List[str]] = None


@router.get("/")
async def get_constitution(
    db: AsyncSession = Depends(get_db)
):
    """Get the current governance constitution."""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "governance_constitution")
    )
    config = result.scalar_one_or_none()
    
    if config:
        try:
            return json.loads(config.value)
        except:
            pass
    
    # Default constitution
    return {
        "version": "1.0.0",
        "principles": {
            "privacy_first": True,
            "sovereignty": True,
            "transparency": True,
            "auditability": True,
            "explainability": True
        },
        "policies": {
            "data_retention_days": 365,
            "requires_human_approval": False,
            "auto_crystallization": True,
            "crystallization_threshold": 0.85,
            "max_confidence_threshold": 0.95
        },
        "temperature": {
            "energy_level": 0.7,
            "vibration": 0.5,
            "description": "Balanced thermodynamic state - optimal for learning and crystallization"
        },
        "rules": [
            "All decisions must be traceable",
            "User data is sovereign and non-transferable",
            "AI decisions must be explainable on demand",
            "Crystallization requires a confidence score above threshold"
        ]
    }


@router.put("/")
async def update_constitution(
    update: ConstitutionUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update the governance constitution (admin only)."""
    # Get current constitution
    current = await get_constitution(db)
    
    # Merge updates
    if update.version is not None:
        current["version"] = update.version
    if update.principles is not None:
        current["principles"] = update.principles
    if update.policies is not None:
        current["policies"] = update.policies
    if update.temperature is not None:
        current["temperature"] = update.temperature.dict()
    if update.rules is not None:
        current["rules"] = update.rules
    
    # Save to database
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "governance_constitution")
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = json.dumps(current)
    else:
        config = SystemConfig(
            key="governance_constitution",
            value=json.dumps(current)
        )
        db.add(config)
    
    await db.commit()
    
    return {"status": "success", "constitution": current}


@router.patch("/temperature")
async def update_temperature(
    temperature: TemperatureControl,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update thermodynamic temperature controls.
    Higher energy/vibration = more active crystallization.
    """
    # Get current constitution
    current = await get_constitution(db)
    
    # Update temperature
    current["temperature"] = temperature.dict()
    
    # Auto-adjust threshold based on energy
    energy = temperature.energy_level
    current["policies"]["crystallization_threshold"] = 0.85 - (energy * 0.2)
    
    # Save
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "governance_constitution")
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = json.dumps(current)
    else:
        config = SystemConfig(
            key="governance_constitution",
            value=json.dumps(current)
        )
        db.add(config)
    
    await db.commit()
    
    return {
        "status": "success",
        "temperature": current["temperature"],
        "crystallization_threshold": current["policies"]["crystallization_threshold"]
    }


@router.get("/temperature")
async def get_temperature(
    db: AsyncSession = Depends(get_db)
):
    """Get current temperature controls."""
    constitution = await get_constitution(db)
    return {
        "temperature": constitution.get("temperature", {}),
        "crystallization_threshold": constitution.get("policies", {}).get("crystallization_threshold", 0.85)
    }


@router.get("/validate")
async def validate_constitution(
    db: AsyncSession = Depends(get_db)
):
    """Validate the current constitution for compliance."""
    constitution = await get_constitution(db)
    issues = []
    
    # Check required fields
    required_fields = ["version", "principles", "policies", "rules"]
    for field in required_fields:
        if field not in constitution:
            issues.append(f"Missing required field: {field}")
    
    # Check temperature is valid
    temp = constitution.get("temperature", {})
    if temp:
        energy = temp.get("energy_level", 0.5)
        vibration = temp.get("vibration", 0.5)
        if not (0.0 <= energy <= 1.0) or not (0.0 <= vibration <= 1.0):
            issues.append("Temperature values must be between 0 and 1")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "constitution": constitution
    }
