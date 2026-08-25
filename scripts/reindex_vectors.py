import sys
import asyncio
import os
import httpx
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models import Memory
from app.repositories.faiss.vector import FAISSSemanticRepository
from sqlalchemy import select

async def reindex():
    print("🧹 Cleaning up old index...")
    base_dir = '/home/rajinderj8888/personavault/backend/storage'
    idx_path = os.path.join(base_dir, 'vector_index.faiss')
    meta_path = os.path.join(base_dir, 'vector_metadata.pkl')
    
    if os.path.exists(idx_path): os.remove(idx_path)
    if os.path.exists(meta_path): os.remove(meta_path)

    print("🚀 Re-indexing memories...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Initialize repository
        repo = FAISSSemanticRepository(index_path=idx_path, metadata_path=meta_path, client=client)
        repo._create_new_index()
        
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
                    
        repo._save_index()
        print(f"✅ Successfully indexed {count} memories.")

if __name__ == "__main__":
    asyncio.run(reindex())
