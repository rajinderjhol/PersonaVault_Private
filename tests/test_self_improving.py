"""
Validation tests for Self-Improving Intelligence.
"""
import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.self_improving import SelfImprovingIntelligence
from app.models import SemanticPattern

@pytest.mark.asyncio
async def test_learning_loop(db_session: AsyncSession):
    """
    1. Simulate interaction
    2. Check if pattern created
    3. Reinforce pattern
    4. Verify weight increase
    """
    service = SelfImprovingIntelligence(db_session)
    await service.initialize()
    
    # 1. Simulate a success pattern
    await service.analyze_interaction(
        user_id=1,
        query="security alert: phishing detected",
        response="Block the sender and rotate credentials.",
        confidence=0.95
    )
    
    # 2. Verify pattern creation
    patterns = await service.get_active_patterns()
    phishing_pattern = next((p for p in patterns if "phishing" in p["trigger"]), None)
    assert phishing_pattern is not None
    initial_weight = phishing_pattern["weight"]
    
    # 3. Reinforce pattern (simulated success)
    await service.analyze_interaction(
        user_id=1,
        query="security alert: phishing detected",
        response="Block the sender and rotate credentials.",
        confidence=0.98
    )
    
    # 4. Verify reinforcement
    patterns = await service.get_active_patterns()
    updated_pattern = next((p for p in patterns if p["id"] == phishing_pattern["id"]), None)
    assert updated_pattern["weight"] > initial_weight
    print(f"\n✅ Reinforcement validated. Weight increased from {initial_weight:.2f} to {updated_pattern['weight']:.2f}")
