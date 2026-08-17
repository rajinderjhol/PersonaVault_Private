#!/usr/bin/env python3
"""
Seed contract memories into the database.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from sqlalchemy import select, func

async def seed_contract_memories():
    async with SessionLocal() as db:
        # Check if contract memories already exist
        result = await db.execute(select(func.count(Memory.id)).where(Memory.tags.like('%contract%')))
        count = result.scalar_one()
        
        if count > 0:
            print(f"   ℹ️  Contract memories already exist ({count} found)")
            return
        
        # Create contract memories
        memories = [
            Memory(
                user_id=1,
                title="Vendor Contract - XYZ Corp",
                content="Contract with XYZ Corp signed June 2026. Annual commitment: $500,000. Services: cloud infrastructure. Term: 2 years with auto-renewal clause.",
                tags="contract,vendor,renewal"
            ),
            Memory(
                user_id=1,
                title="Client Agreement - Acme Corporation",
                content="Acme Corporation agreement for software development services. Scope: 12-month project. Payment: $150,000 total, net 30 terms.",
                tags="contract,client,payment"
            ),
            Memory(
                user_id=1,
                title="NDA - Standard Mutual",
                content="Standard NDA template used for all vendor relationships. Mutual confidentiality, 5-year term, standard exceptions for public information.",
                tags="contract,nda,confidentiality"
            ),
            Memory(
                user_id=1,
                title="Service Level Agreement - Cloud Services",
                content="SLA for cloud services: 99.95% uptime guarantee, 2-hour response for critical issues, 24-hour resolution target.",
                tags="contract,sla,service"
            ),
            Memory(
                user_id=1,
                title="Procurement Review - FastLogistics",
                content="3 suppliers evaluated for logistics contract. Top choice: FastLogistics. Projected savings: 15%. Contract value: $2.5M.",
                tags="contract,procurement,vendor"
            ),
            Memory(
                user_id=1,
                title="My Profile - Rajinder",
                content="I'm a developer working on PersonaVault, an AI-powered memory and decision platform. I prefer detailed technical explanations.",
                tags="personal,profile,preferences"
            ),
            Memory(
                user_id=1,
                title="Security Incident - July 2026",
                content="Security incident on July 28: Phishing email detected targeting finance team. Escalated and blocked. Incident response time: 15 minutes.",
                tags="security,incident,response"
            ),
        ]
        
        db.add_all(memories)
        await db.commit()
        print(f"   ✅ Created {len(memories)} contract and profile memories")

if __name__ == "__main__":
    asyncio.run(seed_contract_memories())
