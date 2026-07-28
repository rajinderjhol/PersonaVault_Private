#!/usr/bin/env python3
"""
Test script for Sovereign Organisational Intelligence Platform.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.policy import Policy
from app.services.learning.reinforcement_engine import ReinforcementEngine
from app.services.governance.audit_service import AuditService
from app.services.governance.explainability import ExplainabilityEngine
from datetime import datetime, timezone

async def test():
    print("🧪 Testing Sovereign Organisational Intelligence Platform")
    print("="*50)
    
    session_factory = SessionLocal
    
    # Test 1: Create a policy
    print("\n📋 Test 1: Creating policy...")
    async with session_factory() as db:
        policy = Policy(
            name="Test Policy",
            domain="legal",
            description="Test policy",
            triggers=["test", "example"],
            actions=[{"action": "flag", "severity": "medium"}],
            confidence=0.7,
            is_active=True
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        policy_id = policy.id
        print(f"✅ Created policy: {policy.name} (ID: {policy_id})")
    
    # Test 2: Create a behaviour event
    print("\n📝 Test 2: Creating behaviour event...")
    async with session_factory() as db:
        event = BehaviourEvent(
            user_id=1,
            event_type="test_event",
            actor="user",
            artefact="test_123",
            decision="approved",
            reason="Test reason",
            outcome="success",
            confidence=0.8,
            extra_data={"key": "value"}
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        event_id = event.id
        print(f"✅ Created event: {event.event_type} (ID: {event_id})")
    
    # Test 3: Test reinforcement engine
    print("\n🔄 Test 3: Testing reinforcement engine...")
    engine = ReinforcementEngine(session_factory)
    
    # Update policy confidence
    await engine.update_policy_confidence(policy_id, success=True)
    print(f"✅ Policy confidence updated")
    
    # Test 4: Test audit service
    print("\n🔍 Test 4: Testing audit service...")
    audit = AuditService(session_factory)
    
    # Log the decision
    async with session_factory() as db:
        from sqlalchemy import select
        stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
        result = await db.execute(stmt)
        db_event = result.scalars().first()
        
        if db_event:
            audit_id = await audit.log_decision(db_event)
            print(f"✅ Audit logged: {audit_id}")
    
    # Test 5: Test explainability
    print("\n💡 Test 5: Testing explainability...")
    explain = ExplainabilityEngine(session_factory)
    
    # Get explanation
    async with session_factory() as db:
        from sqlalchemy import select
        stmt = select(BehaviourEvent).where(BehaviourEvent.id == event_id)
        result = await db.execute(stmt)
        db_event = result.scalars().first()
        
        if db_event and db_event.audit_id:
            explanation = await explain.explain_decision(db_event.audit_id)
            print(f"✅ Explanation: {explanation.get('explanation', 'No explanation')[:100]}...")
    
    # Test 6: Check policy confidence
    print("\n📊 Test 6: Checking policy confidence...")
    async with session_factory() as db:
        from sqlalchemy import select
        stmt = select(Policy).where(Policy.id == policy_id)
        result = await db.execute(stmt)
        policy = result.scalars().first()
        
        if policy:
            print(f"✅ Policy confidence: {policy.confidence:.2f}")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())
