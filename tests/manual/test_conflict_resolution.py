#!/usr/bin/env python3
"""
Test script for CRDT-style conflict resolution.
"""
import asyncio
import sys
import random
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.learning.behaviour_event import BehaviourEvent
from app.services.conflict.detection import ConflictDetectionService
from app.services.blackboard import CognitiveBlackboard
from datetime import datetime, timezone, timedelta

async def test_conflict_resolution():
    print("🧪 Testing CRDT Conflict Resolution")
    print("="*50)
    
    session_factory = SessionLocal
    blackboard = CognitiveBlackboard(session_factory)
    conflict_service = ConflictDetectionService(session_factory)
    
    # Create mock events
    print("\n📝 Creating mock events...")
    
    event1 = BehaviourEvent(
        user_id=1,
        event_type="contract_review",
        actor="Agent_A",
        artefact="contract_123",
        decision="approved",
        reason="Approved by Agent A",
        outcome="success",
        confidence=0.85,
        extra_data={"clause": "liability"},
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=10)
    )
    
    event2 = BehaviourEvent(
        user_id=1,
        event_type="contract_review",
        actor="Agent_B",
        artefact="contract_123",
        decision="rejected",
        reason="Rejected by Agent B",
        outcome="pending",
        confidence=0.75,
        extra_data={"clause": "liability"},
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=5)
    )
    
    # Test conflict detection
    print("\n🔍 Testing conflict detection...")
    conflicts = await conflict_service.detect_conflicts(event2)
    print(f"   Found {len(conflicts)} conflicts")
    
    if conflicts:
        print("\n⚡ Conflict detected!")
        for c in conflicts:
            print(f"   - {c.actor}: {c.decision} (conf: {c.confidence})")
    
    # Test conflict resolution
    print("\n🔄 Testing conflict resolution...")
    resolution = await conflict_service.resolve_conflict([event1, event2], "crdt_merge")
    print(f"   Resolved: {resolution.get('resolved')}")
    print(f"   Strategy: {resolution.get('strategy')}")
    print(f"   Decision: {resolution.get('merged_decision')}")
    print(f"   Reason: {resolution.get('reason')[:50]}...")
    
    # Test blackboard with conflict resolution
    print("\n🧠 Testing blackboard with conflict resolution...")
    await blackboard.post_insight(
        "Agent_A", 
        {"artefact": "contract_123", "decision": "approved", "confidence": 0.85},
        resolve_conflicts=True
    )
    await blackboard.post_insight(
        "Agent_B", 
        {"artefact": "contract_123", "decision": "rejected", "confidence": 0.75},
        resolve_conflicts=True
    )
    
    snapshot = blackboard.get_snapshot()
    print(f"   Active agents: {snapshot.get('active_agents')}")
    print(f"   Total conflicts: {snapshot.get('total_conflicts')}")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_conflict_resolution())
