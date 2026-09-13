import asyncio
import pytest
import os
import faiss
from app.repositories.faiss.vector import FAISSSemanticRepository

@pytest.mark.asyncio
async def test_vector_index_persistence():
    repo_path = "storage/test_vector_index.faiss"
    meta_path = "storage/test_vector_metadata.pkl"
    
    # Ensure clean state
    if os.path.exists(repo_path): os.remove(repo_path)
    if os.path.exists(meta_path): os.remove(meta_path)
    
    # 1. Initialize repo
    repo = FAISSSemanticRepository(index_path=repo_path, metadata_path=meta_path)
    
    # 2. Add a vector
    # Manually ensure embedding is not zero
    import numpy as np
    emb = np.random.rand(768).astype(np.float32)
    repo.index.add(emb.reshape(1, -1))
    repo.metadata[0] = {"id": 1, "content": "test"}
    repo._save_index()
    
    assert os.path.exists(repo_path)
    print(f"\nDEBUG: File size after save: {os.path.getsize(repo_path)}")
    
    # 3. Force reload
    repo2 = FAISSSemanticRepository(index_path=repo_path, metadata_path=meta_path)
    
    print(f"DEBUG: Index total after reload: {repo2.index.ntotal}")
    assert repo2.index.ntotal == 1
    
    # Cleanup
    if os.path.exists(repo_path): os.remove(repo_path)
    if os.path.exists(meta_path): os.remove(meta_path)
