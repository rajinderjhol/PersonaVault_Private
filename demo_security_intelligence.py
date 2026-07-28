#!/usr/bin/env python3
"""
Security Intelligence Demo Script
Uses direct database access for reliability.
"""
import asyncio
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.learning.behaviour_event import BehaviourEvent
from app.services.learning.timeline_service import TimelineService
from app.services.learning.replay_service import ReplayService
from app.services.governance.audit_service import AuditService
from app.services.governance.explainability import ExplainabilityEngine

async def demo():
    print("="*60)
    print("🔐 Security Intelligence Pack - Decision Timeline Demo")
    print("="*60)
    
    session_factory = SessionLocal
    
    # Step 1: Create security incident
    print("\n📝 Step 1: Creating Security Incident...")
    
    async with session_factory() as db:
        event = BehaviourEvent(
            user_id=1,
            event_type="incident_response",
            actor="soc_analyst",
            artefact="incident_001",
            decision="escalated",
            reason="Phishing attempt detected, escalated to SOC lead",
            outcome="success",
            confidence=0.91,
            extra_data={
                "incident_type": "phishing",
                "severity": "high",
                "time_to_detect": 120,
                "sender": "attacker@example.com",
                "recipient": "user@company.com",
                "subject": "Urgent: Account verification required"
            }
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        event_id = event.id
        
        # Log audit
        audit = AuditService(session_factory)
        audit_id = await audit.log_decision(event)
        
        print(f"✅ Incident created: ID={event_id}, Audit={audit_id}")
    
    # Step 2: Build timeline
    print("\n⏳ Step 2: Building Decision Timeline...")
    
    async with session_factory() as db:
        service = TimelineService(session_factory)
        timeline = await service.build_timeline(event)
        print(f"✅ Timeline built with {len(timeline)} steps")
    
    # Step 3: Display timeline
    print("\n📊 Step 3: Decision Timeline")
    print("-"*50)
    
    for step in timeline:
        icon = "🔍" if step["type"] == "detection" else "📋" if step["type"] == "policy_match" else "🤖" if step["type"] == "ai_recommendation" else "👤" if step["type"] == "decision" else "🔒" if step["type"] == "audit" else "📚" if step["type"] == "learning" else "•"
        print(f"{icon} {step['step']}. {step['label']}")
        print(f"   {step['description']}")
        if step.get("confidence"):
            print(f"   Confidence: {step['confidence']*100:.0f}%")
        print()
    
    # Step 4: Explainability
    print("\n💡 Step 4: Decision Explanation")
    print("-"*50)
    
    async with session_factory() as db:
        explain = ExplainabilityEngine(session_factory)
        explanation = await explain.explain_decision(audit_id)
        if "explanation" in explanation:
            print(f"📝 {explanation['explanation']}")
    
    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print(f"🔍 View the full timeline in the dashboard")
    print(f"📋 Audit ID: {audit_id}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(demo())
