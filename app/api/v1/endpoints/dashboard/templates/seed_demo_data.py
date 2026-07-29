"""Seed the system with rich demo data."""
import asyncio
import sys
import os

# Adjust the path to import from the app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from db.session import SessionLocal
from models import Memory
from sqlalchemy import select, func

async def seed():
    async with SessionLocal() as db:
        # Check if already seeded
        count_result = await db.execute(select(func.count(Memory.id)))
        if count_result.scalar_one() > 0:
            print("✅ Already seeded with memories. Skipping demo data creation.")
            return
        
        # Create 10 sample memories
        sample_memories = [
            "Security incident on July 28: A phishing email was detected targeting finance team. The incident was escalated and blocked.",
            "Contract review for Vendor ABC completed. Contract approved with liability cap of $5M.",
            "GDPR compliance review found Article 5 violation in customer data processing. Issue flagged for remediation.",
            "IoT device temperature spike detected at 42°C. Alert sent to maintenance team. No action required.",
            "User feedback: 'The AI is getting smarter! It remembered my preference for detailed security reports.'",
            "Procurement review: 3 suppliers evaluated for logistics contract. Top choice identified.",
            "Insurance claim #1234 reviewed. Claim approved for $12,500 based on policy terms.",
            "Compliance audit completed. 4 findings identified, 2 critical, 2 minor.",
            "Security incident response time improved to 15 minutes (down from 45 minutes).",
            "Contract renewal for Vendor XYZ: Terms renegotiated, 15% cost reduction achieved."
        ]
        for i, content in enumerate(sample_memories):
            m = Memory(user_id=1, title=content[:50], content=content, tags="sample", modality="text")
            db.add(m)
        await db.commit()
        print(f"✅ Created {len(sample_memories)} sample memories for first-time user.")

if __name__ == "__main__":
    asyncio.run(seed())