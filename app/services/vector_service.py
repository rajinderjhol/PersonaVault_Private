import os
import logging
import numpy as np
import faiss
import pickle
import httpx
import time
from config import Config
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VectorService:
    """FAISS-based vector search for semantic memory retrieval."""
    
    def __init__(self, index_path: str = "storage/vector_index.faiss", 
                 metadata_path: str = "storage/vector_metadata.pkl",
                 client: Optional[httpx.AsyncClient] = None):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self._client = client
        self.index = None
        self.metadata = {}
        self.dimension = getattr(Config, "OLLAMA_EMBEDDING_DIM", 768)
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"VectorService: Loaded index from {self.index_path} with {len(self.metadata)} entries")
            except Exception as e:
                logger.error(f"Failed to load vector index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        logger.info("VectorService: Initialized new flat L2 index")
    
    def _save_index(self):
        """Save index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from local Ollama instance."""
        try:
            response = await self._client.post(
                f"{Config.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": Config.OLLAMA_EMBEDDING_MODEL, "prompt": text},
                timeout=10.0
            )
            
            if response.status_code == 200:
                embedding = response.json().get("embedding", [])
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"VectorService: Ollama embedding error: {e}")
        # Fallback to zero vector if Ollama is unreachable
        return np.zeros(self.dimension).astype(np.float32)
    
    async def index_memory(self, memory_id: int, content: str, user_id: int):
        """Index a new memory in the FAISS store."""
        embedding = await self._get_embedding(content)
        
        if np.all(embedding == 0):
            logger.warning(f"VectorService: Skipping indexing for memory_id={memory_id} because embedding failed (Ollama may be offline)")
            return

        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)  # Normalize
        self.index.add(embedding.reshape(1, -1))
        
        idx = self.index.ntotal - 1
        self.metadata[idx] = {
            "id": memory_id,
            "content": content,
            "user_id": user_id
        }
        self._save_index()
        logger.info(f"VectorService: Indexed memory_id={memory_id} for user_id={user_id}")
    
    async def search_similar(self, query: str, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for memories using semantic similarity."""
        if self.index.ntotal == 0:
            return []
        
        start_time = time.perf_counter()
        embedding = await self._get_embedding(query)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
        
        distances, indices = self.index.search(embedding.reshape(1, -1), min(limit, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata:
                meta = self.metadata[idx]
                if meta["user_id"] == user_id:
                    results.append({
                        "id": meta["id"],
                        "content": meta["content"],
                        "score": float(1 / (1 + distances[0][i]))
                    })
        
        end_time = time.perf_counter()
        logger.info(f"VectorService: Search completed in {end_time - start_time:.4f}s. Results found: {len(results)}")
        return results

    def check_health(self) -> bool:
        """Verify FAISS index is loaded."""
        index_ok = self.index is not None
        # We can also verify if we have a client to talk to AI services
        return index_ok and self._client is not None

# Instantiate a global service instance for use throughout the application
vector_service = VectorService()