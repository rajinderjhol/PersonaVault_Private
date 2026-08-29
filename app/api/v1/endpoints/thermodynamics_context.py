"""
Thermodynamic API Context Endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/thermodynamics", tags=["thermodynamics"])

@router.get("/current-decision")
async def get_current_decision():
    """Mock for active decision context."""
    return {
        "step": "ai_recommendation",
        "confidence": 88,
        "agent": "Security Agent",
        "timestamp": "2026-08-29T14:32:18Z",
        "policy": "Security Policy v2.3",
        "trace": {
            "perception": True,
            "policy_match": True,
            "ai_recommendation": True,
            "action": False,
            "outcome": False
        }
    }

@router.get("/active-snowflake")
async def get_active_snowflake():
    """Mock for active snowflake context."""
    return {
        "domain": "security",
        "focus": "Threat detection, incident response",
        "pattern_count": 10,
        "confidence": 85.0,
        "keywords": ["security", "threat", "breach", "malware"]
    }
