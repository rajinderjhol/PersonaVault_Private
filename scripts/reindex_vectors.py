import sys
import asyncio
import os
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from app.repositories.faiss.vector import FAISSSemanticRepository
from sqlalchemy import select

async def reindex():
    print("🧹 Cleaning up old index...")
    if os.path.exists("storage/vector_index.faiss"):
        os.remove("storage/vector_index.faiss")
    if os.path.exists("storage/vector_metadata.pkl"):
        os.remove("storage/vector_metadata.pkl")

    print("🚀 Re-indexing memories...")
    # Initialize repository - this will create a fresh index
    repo = FAISSSemanticRepository(client=None)
    
    async with SessionLocal() as db:
        stmt = select(Memory)
        results = await db.execute(stmt)
        memories = results.scalars().all()
        
        count = 0
        for m in memories:
            if m.content:
                print(f"  - Adding memory {m.id}...")
                await repo.add(m.id, m.content, m.user_id)
                count += 1
                
    print(f"✅ Successfully indexed {count} memories.")

if __name__ == "__main__":
    asyncio.run(reindex())
