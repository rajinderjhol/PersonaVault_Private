#!/usr/bin/env python3
"""
Create bulk events across multiple domains.
"""
import asyncio
import sys
import random
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.learning.behaviour_event import BehaviourEvent
from app.services.governance.audit_service import AuditService

async def create_events():
    session_factory = SessionLocal
    total = 0
    
    # Security events
    for i in range(5):
        async with session_factory() as db:
            event = BehaviourEvent(
                user_id=1,
                event_type="incident_response",
                actor="soc_analyst",
                artefact=f"incident_{100+i}",
                decision="escalated",
                reason=f"Security incident {i+1} detected",
                outcome="success",
                confidence=0.88 + (i * 0.01),
                extra_data={
                    "incident_type": "phishing",
                    "severity": "high" if i % 2 == 0 else "medium",
                    "iteration": i
                }
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            total += 1
            print(f"✅ Security event {i+1}: {event.id}")
    
    # Contract events
    for i in range(5):
        async with session_factory() as db:
            event = BehaviourEvent(
                user_id=1,
                event_type="contract_review",
                actor="legal_reviewer",
                artefact=f"contract_{200+i}",
                decision="rejected" if i % 2 == 0 else "approved",
                reason=f"Contract review {i+1} completed",
                outcome="success",
                confidence=0.85 + (i * 0.02),
                extra_data={
                    "clause": "liability" if i % 2 == 0 else "indemnity",
                    "risk_level": 0.7 + (i * 0.05),
                    "iteration": i
                }
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            total += 1
            print(f"✅ Contract event {i+1}: {event.id}")
    
    # Compliance events
    for i in range(3):
        async with session_factory() as db:
            event = BehaviourEvent(
                user_id=1,
                event_type="compliance_review",
                actor="compliance_officer",
                artefact=f"policy_{300+i}",
                decision="approved",
                reason=f"Compliance check {i+1} passed",
                outcome="success",
                confidence=0.93 + (i * 0.01),
                extra_data={
                    "policy_id": f"POL-{300+i}",
                    "checks_passed": 5 + i,
                    "iteration": i
                }
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            total += 1
            print(f"✅ Compliance event {i+1}: {event.id}")
    
    # Insurance events
    for i in range(2):
        async with session_factory() as db:
            event = BehaviourEvent(
                user_id=1,
                event_type="underwriting_decision",
                actor="underwriter",
                artefact=f"policy_{400+i}",
                decision="approved",
                reason=f"Underwriting decision {i+1}",
                outcome="success",
                confidence=0.90 + (i * 0.02),
                extra_data={
                    "policy_type": "commercial",
                    "coverage_amount": 500000 + (i * 100000),
                    "risk_score": 0.3 - (i * 0.05),
                    "iteration": i
                }
            )
            db.add(event)
            await db.commit()
            await db.refresh(event)
            total += 1
            print(f"✅ Insurance event {i+1}: {event.id}")
    
    print(f"\n✅ Total events created: {total}")

if __name__ == "__main__":
    asyncio.run(create_events())
