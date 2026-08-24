"""Seed the system with comprehensive demo data for all tables."""
import asyncio
import sys
import json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import (
    Memory, User, Organization, SystemConfig,
    BehaviourEvent, DecisionTrajectory, Policy, BehaviourPack
)
from sqlalchemy import select, func
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_all():
    print("🌱 Seeding comprehensive demo data...")
    
    async with SessionLocal() as db:
        # 1. Check if already seeded
        count_result = await db.execute(select(func.count(Memory.id)))
        memory_count = count_result.scalar_one()
        
        if memory_count > 0:
            print(f"✅ Already seeded ({memory_count} memories)")
            return
        
        # 2. Create Organization
        org = Organization(name="Default Organization", slug="default")
        db.add(org)
        await db.flush()
        
        # 3. Create User
        user = User(
            username="admin",
            email="admin@personavault.local",
            hashed_password=pwd_context.hash("admin123"),
            role="admin",
            organization_id=org.id,
            is_active=True
        )
        db.add(user)
        await db.flush()
        
        # 4. Create Behaviour Events
        behaviour_events = [
            BehaviourEvent(
                user_id=user.id,
                                event_type="incident_response",
                decision="blocked",
                confidence=0.92,
                timestamp=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="incident_response",
                decision="blocked",
                confidence=0.95,
                timestamp=datetime.now(timezone.utc) - timedelta(hours=2)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="compliance_review",
                decision="approved",
                confidence=0.88,
                timestamp=datetime.now(timezone.utc) - timedelta(days=3)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="contract_review",
                decision="approved",
                confidence=0.91,
                timestamp=datetime.now(timezone.utc) - timedelta(days=7)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="procurement_decision",
                decision="approved",
                confidence=0.82,
                timestamp=datetime.now(timezone.utc) - timedelta(days=14)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="incident_response",
                decision="escalated",
                confidence=0.87,
                timestamp=datetime.now(timezone.utc) - timedelta(days=5)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="compliance_review",
                decision="rejected",
                confidence=0.95,
                timestamp=datetime.now(timezone.utc) - timedelta(days=4)
            ),
            BehaviourEvent(
                user_id=user.id,
                                event_type="contract_review",
                decision="rejected",
                confidence=0.85,
                timestamp=datetime.now(timezone.utc) - timedelta(days=2)
            ),
        ]
        db.add_all(behaviour_events)
        
        # 5. Create Sample Memories
        sample_memories = [
            "Security incident on July 28: A phishing email was detected targeting finance team.",
            "Contract review for Vendor ABC completed. Approved with liability cap of $5M.",
            "GDPR compliance review found Article 5 violation in customer data processing.",
            "IoT device temperature spike detected at 42°C. Alert sent to maintenance team.",
            "Procurement review: 3 suppliers evaluated for logistics contract.",
            "Insurance claim #1234 reviewed. Claim approved for $12,500.",
            "Compliance audit completed. 4 findings identified, 2 critical, 2 minor.",
            "Security incident response time improved to 15 minutes (down from 45 minutes).",
            "Contract renewal for Vendor XYZ: Terms renegotiated, 15% cost reduction.",
            "User feedback: 'The AI is getting smarter!'"
        ]
        
        for content in sample_memories:
            m = Memory(
                user_id=user.id,
                title=content[:50] + ("..." if len(content) > 50 else ""),
                content=content,
                tags="sample,demo",
                modality="text"
            )
            db.add(m)
        
        await db.commit()
        print(f"✅ Created {len(behaviour_events)} behaviour events")
        print(f"✅ Created {len(sample_memories)} sample memories")
        print(f"✅ Created 1 user and 1 organization")

if __name__ == "__main__":
    asyncio.run(seed_all())
