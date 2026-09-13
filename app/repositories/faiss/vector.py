import os
import logging
import numpy as np
import faiss
import pickle
import httpx
from typing import List, Dict, Any, Optional
from app.repositories.interfaces import IVectorRepository
from app.config import Config

logger = logging.getLogger(__name__)

class FAISSSemanticRepository(IVectorRepository):
    """FAISS implementation for semantic memory (Layer 3)."""
    
    def __init__(self, 
                 index_path: str = "/home/rajinderj8888/personavault/backend/storage/vector_index.faiss", 
                 metadata_path: str = "/home/rajinderj8888/personavault/backend/storage/vector_metadata.pkl",
                 client: Optional[httpx.AsyncClient] = None):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._client = client
        self.index = None
        self.metadata = {}
        self.dimension = getattr(Config, "OLLAMA_EMBEDDING_DIM", 768)
        self._load_or_create_index()

    def _load_or_create_index(self):
        try:
            logger.info(f"Loading index from {self.index_path}")
            logger.info(f"DEBUG: CWD is {os.getcwd()}")
            logger.info(f"DEBUG: Absolute index path: {os.path.abspath(self.index_path)}")
            logger.info(f"DEBUG: Absolute metadata path: {os.path.abspath(self.metadata_path)}")
            
            logger.info(f"Index path exists: {os.path.exists(self.index_path)}")
            logger.info(f"Metadata path exists: {os.path.exists(self.metadata_path)}")
            
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Index loaded successfully. Total: {self.index.ntotal}")
            else:
                logger.info("Index files not found, creating new index.")
                raise FileNotFoundError("Index or metadata files missing.")
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}. Creating a new index.")
            self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        # V3 Fix: Durability gap - ensure new index is persisted immediately
        self._save_index()

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    async def _get_embedding(self, text: str) -> np.ndarray:
        try:
            if not self._client:
                return np.zeros(self.dimension).astype(np.float32)
            response = await self._client.post(
                f"{Config.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": Config.OLLAMA_EMBEDDING_MODEL, "prompt": text},
                timeout=10.0
            )
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"FAISSSemanticRepository: Embedding error: {e}")
        return np.zeros(self.dimension).astype(np.float32)

    async def add(self, memory_id: int, content: str, user_id: int, environment_id: Optional[str] = None) -> bool:
        embedding = await self._get_embedding(content)
        if np.all(embedding == 0):
            return False

        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
        self.index.add(embedding.reshape(1, -1))
        
        idx = self.index.ntotal - 1
        self.metadata[idx] = {
            "id": memory_id,
            "content": content,
            "user_id": user_id,
            "environment_id": environment_id
        }
        self._save_index()
        return True

    async def search(self, query: str, user_id: int, limit: int = 10, environment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
        
        embedding = await self._get_embedding(query)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
        
        distances, indices = self.index.search(embedding.reshape(1, -1), min(limit * 2, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata:
                meta = self.metadata[idx]
                
                # Check user_id
                if meta["user_id"] != user_id:
                    continue
                
                # Check environment_id
                if environment_id and meta.get("environment_id") != environment_id:
                    continue
                
                results.append({
                    "id": meta["id"],
                    "content": meta["content"],
                    "score": float(1 / (1 + distances[0][i])),
                    "metadata": {"environment_id": meta.get("environment_id")}
                })
                
                if len(results) >= limit:
                    break
                    
        return results

    async def delete(self, memory_id: int) -> bool:
        # FAISS IndexFlatL2 doesn't support easy deletion by ID without rebuilding.
        # For now, we just mark it as deleted in metadata if we wanted to, 
        # or rebuild the index. Rebuilding is expensive.
        # Simplified: Filter out during search or rebuild periodically.
        return False
