import sys
import asyncio
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from sqlalchemy import select

async def add_legal_cases():
    print("🚀 Seeding Legal Domain Data...")
    
    legal_cases = [
        {
            'title': 'IP infringement claim - Vendor XYZ',
            'content': 'Case #2026-001: IP infringement claim against vendor XYZ. Filed June 15, 2026. Status: Discovery phase. Estimated resolution: Q4 2026.',
            'tags': 'legal,contracts,ip'
        },
        {
            'title': 'Contract dispute - Supplier ABC',
            'content': 'Case #2026-002: Contract dispute with supplier ABC. Filed July 1, 2026. Status: Mediation scheduled for Sept 2026. Claim amount: $500,000.',
            'tags': 'legal,contracts,dispute'
        },
        {
            'title': 'Employment discrimination claim',
            'content': 'Case #2026-003: Employment discrimination claim. Filed March 2026. Status: Dismissed with prejudice. No liability found.',
            'tags': 'legal,hr'
        }
    ]
    
    async with SessionLocal() as db:
        for case in legal_cases:
            memory = Memory(
                user_id=1,
                title=case['title'],
                content=case['content'],
                tags=case['tags']
            )
            db.add(memory)
        
        await db.commit()
    print('✅ Legal cases seeded to database')

if __name__ == "__main__":
    asyncio.run(add_legal_cases())
