#!/usr/bin/env python3
"""
Robotics Intelligence Pack - Demo Script
"""
import asyncio
import sys
import random
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.learning.behaviour_event import BehaviourEvent
from app.services.learning.timeline_service import TimelineService
from app.services.governance.audit_service import AuditService
from app.services.governance.explainability import ExplainabilityEngine

async def demo():
    print("="*60)
    print("🦾 Robotics Intelligence Pack Demo")
    print("="*60)
    
    session_factory = SessionLocal
    audit = AuditService(session_factory)
    explain = ExplainabilityEngine(session_factory)
    
    # User scenarios
    scenarios = [
        {
            "event_type": "robot_decision",
            "actor": "robot_assistant",
            "artefact": "navigation",
            "decision": "navigate",
            "reason": "Obstacle detected, rerouting",
            "confidence": 0.95,
            "extra_data": {
                "context": "Patient room 304",
                "options": ["path_a", "path_b"],
                "selected": "path_b",
                "reasoning": "Path A obstructed"
            }
        },
        {
            "event_type": "user_interaction",
            "actor": "robot_assistant",
            "artefact": "conversation_001",
            "decision": "interact",
            "reason": "User requested assistance",
            "confidence": 0.88,
            "extra_data": {
                "user_id": "U001",
                "duration": 45,
                "satisfaction": 0.92,
                "topic": "medication_reminder"
            }
        },
        {
            "event_type": "safety_alert",
            "actor": "safety_monitor",
            "artefact": "alert_001",
            "decision": "alert",
            "reason": "Unusual movement pattern detected",
            "confidence": 0.91,
            "extra_data": {
                "severity": "high",
                "location": "corridor_3",
                "detection_time": 0.5
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📝 Scenario {i}: {scenario['event_type']}")
        
        async with session_factory() as db:
            event = BehaviourEvent(
                user_id=1,
                event_type=scenario["event_type"],
                actor=scenario["actor"],
                artefact=scenario["artefact"],
                decision=scenario["decision"],
                reason=scenario["reason"],
                outcome="success",
                confidence=scenario["confidence"],
                extra_data=scenario["extra_data"]
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            
            audit_id = await audit.log_decision(event)
            print(f"   ✅ Created event: {event.id}")
            print(f"   📋 Audit: {audit_id}")
            
            # Get explanation
            explanation = await explain.explain_decision(audit_id)
            print(f"   💡 Explanation: {explanation.get('explanation', '')[:100]}...")
    
    print("\n" + "="*60)
    print("🦾 Robotics Intelligence Demo Complete!")
    print("📊 Check the dashboard for full timeline and analytics")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(demo())