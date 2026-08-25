import sys
import asyncio
import os
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from sqlalchemy import select

async def seed_domains():
    print("🚀 Seeding Domain Intelligence Data...")
    
    domain_memories = [
        {"title": "Insurance Coverage", "content": "The standard insurance policy covers all cyber-incidents up to $10M, excluding acts of war.", "tags": "insurance"},
        {"title": "Contract Protocol", "content": "All vendor contracts must be reviewed by the legal team and signed by an authorized signatory.", "tags": "contracts"},
        {"title": "Security Protocol", "content": "SOC team incident response time target for critical issues is < 2 hours.", "tags": "security"},
        {"title": "Compliance Check", "content": "Quarterly compliance audits are mandatory to ensure adherence to GDPR and industry security standards.", "tags": "compliance"},
        {"title": "Robotics Safety", "content": "Robotic units in the lab must remain in 'restricted' mode when human personnel are present.", "tags": "robotics"},
        {"title": "Procurement Strategy", "content": "Supplier evaluations prioritize cost savings, vendor reliability, and data privacy compliance.", "tags": "procurement"}
    ]
    
    async with SessionLocal() as db:
        for m in domain_memories:
            memory = Memory(
                user_id=1,
                title=m["title"],
                content=m["content"],
                tags=m["tags"]
            )
            db.add(memory)
        
        await db.commit()
    
    print("✅ Seeded domain-specific memory data.")

if __name__ == "__main__":
    asyncio.run(seed_domains())
