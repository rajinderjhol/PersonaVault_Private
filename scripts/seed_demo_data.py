"""Seed the system with rich demo data."""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from app.models.learning.behaviour_event import BehaviourEvent
from app.models.learning.decision_timeline import DecisionTimeline
from datetime import datetime, timezone, timedelta

async def seed():
    print("🌱 Seeding demo data...")
    
    async with SessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await db.execute(select(func.count(Memory.id)))
        memory_count = count.scalar_one()
        
        if memory_count > 0:
            print(f"✅ Already seeded ({memory_count} memories)")
            # Check events too
            event_count = await db.execute(select(func.count(BehaviourEvent.id)))
            if event_count.scalar_one() > 0:
                print(f"✅ Events already exist ({event_count.scalar_one()} events)")
                return
        
        # ============================================================
        # Create 10 sample memories
        # ============================================================
        memories = [
            "Security incident on July 28: A phishing email was detected targeting the finance team. The incident was escalated and blocked. No data was compromised.",
            "Contract review for Vendor ABC completed. Contract approved with liability cap of $5M and 3-year term.",
            "GDPR compliance review found Article 5 violation in customer data processing. Issue flagged for remediation.",
            "IoT device temperature spike detected at 42°C. Alert sent to maintenance team. No action required.",
            "User feedback: 'The AI is getting smarter! It remembered my preference for detailed security reports.'",
            "Procurement review: 3 suppliers evaluated for logistics contract. Top choice identified.",
            "Insurance claim #1234 reviewed. Claim approved for $12,500 based on policy terms.",
            "Compliance audit completed. 4 findings identified: 2 critical, 2 minor.",
            "Security incident response time improved to 15 minutes (down from 45 minutes).",
            "Contract renewal for Vendor XYZ: Terms renegotiated, 15% cost reduction achieved."
        ]
        
        created_memories = []
        for i, content in enumerate(memories):
            m = Memory(
                user_id=1, 
                title=content[:50] + ("..." if len(content) > 50 else ""), 
                content=content, 
                tags="sample,demo", 
                modality="text",
                created_at=datetime.now(timezone.utc) - timedelta(days=30 - i*3)
            )
            db.add(m)
            created_memories.append(m)
        
        await db.commit()
        print(f"✅ Created {len(memories)} memories")
        
        # ============================================================
        # Create sample events
        # ============================================================
        events = [
            BehaviourEvent(
                user_id=1,
                event_type="incident_response",
                actor="soc_analyst",
                artefact="incident_001",
                decision="escalated",
                reason="Phishing attempt detected with malicious payload",
                outcome="success",
                confidence=0.91,
                extra_data={"severity": "high", "detection_time": "2 minutes"},
                timestamp=datetime.now(timezone.utc) - timedelta(days=5)
            ),
            BehaviourEvent(
                user_id=1,
                event_type="contract_review",
                actor="legal_analyst",
                artefact="contract_123",
                decision="approved",
                reason="No liability issues found. Terms favorable.",
                outcome="success",
                confidence=0.88,
                extra_data={"clause_count": 42, "review_time": "3 hours"},
                timestamp=datetime.now(timezone.utc) - timedelta(days=3)
            ),
            BehaviourEvent(
                user_id=1,
                event_type="compliance_review",
                actor="compliance_officer",
                artefact="policy_456",
                decision="rejected",
                reason="GDPR compliance violation in data processing",
                outcome="failure",
                confidence=0.95,
                extra_data={"violation": "article_5", "severity": "critical"},
                timestamp=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            BehaviourEvent(
                user_id=1,
                event_type="security_incident",
                actor="security_analyst",
                artefact="incident_002",
                decision="contained",
                reason="Malware detected and isolated",
                outcome="success",
                confidence=0.87,
                extra_data={"malware_type": "ransomware", "containment_time": "8 minutes"},
                timestamp=datetime.now(timezone.utc) - timedelta(hours=12)
            ),
            BehaviourEvent(
                user_id=1,
                event_type="procurement_decision",
                actor="procurement_manager",
                artefact="rfi_789",
                decision="approved",
                reason="Supplier met all requirements",
                outcome="success",
                confidence=0.82,
                extra_data={"suppliers_evaluated": 3, "cost_savings": "15%"},
                timestamp=datetime.now(timezone.utc) - timedelta(hours=6)
            )
        ]
        
        for event in events:
            db.add(event)
        
        await db.commit()
        print(f"✅ Created {len(events)} behaviour events")
        
        # ============================================================
        # Create timeline entries for each event
        # ============================================================
        timeline_count = 0
        for event in events:
            timelines = [
                DecisionTimeline(
                    event_id=event.id,
                    step_number=1,
                    step_type="detection",
                    step_label="🔍 Event Detected",
                    step_description=f"Detected {event.event_type}",
                    confidence=event.confidence,
                    actor=event.actor,
                    timestamp=event.timestamp
                ),
                DecisionTimeline(
                    event_id=event.id,
                    step_number=2,
                    step_type="policy_match",
                    step_label="📋 Policy Matched",
                    step_description="Matched 3 relevant policies",
                    confidence=0.85,
                    actor="policy_engine",
                    timestamp=event.timestamp + timedelta(seconds=30)
                ),
                DecisionTimeline(
                    event_id=event.id,
                    step_number=3,
                    step_type="ai_recommendation",
                    step_label="🤖 AI Recommendation",
                    step_description=f"AI recommended '{event.decision}'",
                    confidence=event.confidence,
                    actor="orchestrator",
                    timestamp=event.timestamp + timedelta(seconds=60)
                ),
                DecisionTimeline(
                    event_id=event.id,
                    step_number=4,
                    step_type="decision",
                    step_label="👤 Decision Made",
                    step_description=f"Decision: {event.decision}",
                    confidence=event.confidence,
                    actor=event.actor,
                    reason=event.reason,
                    timestamp=event.timestamp + timedelta(seconds=120)
                ),
                DecisionTimeline(
                    event_id=event.id,
                    step_number=5,
                    step_type="audit",
                    step_label="🔒 Audit Logged",
                    step_description=f"Audit ID: audit-{event.id:04d}",
                    confidence=1.0,
                    actor="audit_system",
                    timestamp=event.timestamp + timedelta(seconds=180)
                )
            ]
            for tl in timelines:
                db.add(tl)
                timeline_count += 1
        
        await db.commit()
        print(f"✅ Created {timeline_count} timeline entries")
        
        # ============================================================
        # Summary
        # ============================================================
        print("\n📊 Seeding Summary:")
        print(f"   - Memories: {len(memories)}")
        print(f"   - Events: {len(events)}")
        print(f"   - Timeline entries: {timeline_count}")
        print("\n✅ Seeding complete! Your dashboard now has rich demo data.")

if __name__ == "__main__":
    asyncio.run(seed())
