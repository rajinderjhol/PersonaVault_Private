import asyncio
import httpx
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.services.memory_service import MemoryService
from app.services.vector_service import vector_service
from app.services.graph_service import graph_service
from app.db.memory_repository import SQLMemoryRepository
from app.config import Config

async def insert_test_and_verify():
    print("🧪 PersonaVault: Semantic Search Verification Utility")
    
    # Initialize database session
    db = SessionLocal()
    
    try:
        # 1. Initialize shared HTTP client (required by VectorService)
        async with httpx.AsyncClient(timeout=30.0) as client:
            vector_service._client = client
            
            # 2. Ensure vector index is initialized
            print("📊 Initializing vector index...")
            vector_service._load_or_create_index()
            
            # 3. Create repository
            repository = SQLMemoryRepository(
                db=db,
                vector_service=vector_service,
                graph_service=graph_service
            )
            
            # 4. Create memory service with repository
            service = MemoryService(repository=repository)
            
            # 5. User ID 1 is the default admin
            user_id = 1
            
            # 6. Insert unique test content
            test_content = "The administrative override code for the server room is Delta-Seven-Niner-Alpha."
            print(f"\n[1/3] Inserting test memory: '{test_content}'")
            
            try:
                memory = await service.save_memory(
                    user_id=user_id,
                    memory_type="technical",
                    content=test_content,
                    tags=["test", "security", "credential"]
                )
                print(f"✅ Memory saved to SQLite and indexed in FAISS (ID: {memory.id})")
                
                # 7. Verify Semantic Retrieval
                query = "What is the entry code for the server room?"
                print(f"\n[2/3] Testing semantic retrieval for: '{query}'")
                
                results = await service.search_memories(user_id, query)
                
                if results:
                    print(f"✅ SUCCESS: Found {len(results)} matches.")
                    for i, res in enumerate(results):
                        # Handle both dict and object results
                        if isinstance(res, dict):
                            print(f"   {i+1}. [Score: {res.get('score', 0):.4f}] {res.get('content', '')[:80]}")
                        else:
                            print(f"   {i+1}. [Score: {getattr(res, 'score', 0):.4f}] {getattr(res, 'content', '')[:80]}")
                else:
                    print("❌ FAILURE: No matches found. Check if Ollama is running and models are pulled.")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(insert_test_and_verify())
