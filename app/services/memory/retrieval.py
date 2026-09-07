import logging
from typing import List, Dict, Any, Optional
from app.repositories.faiss.vector import IVectorRepository
from app.services.thermodynamics.phase_service import PhaseService

logger = logging.getLogger(__name__)

class MemoryRetrievalService:
    def __init__(self):
        self.vector_repo = IVectorRepository()
        self.phase_service = PhaseService()

    async def retrieve(
        self,
        query: str,
        env_id: str,
        pack_ids: Optional[List[str]] = None,
        layers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from all layers."""
        results = []
        
        # 1. Gas layer (working memory)
        if not layers or "gas" in layers:
            try:
                gas_results = await self.phase_service.get_gas(env_id)
                results.extend(gas_results)
            except Exception as e:
                logger.warning(f"Gas retrieval failed: {e}")
        
        # 2. Liquid layer (episodic)
        if not layers or "liquid" in layers:
            try:
                liquid_results = await self.phase_service.get_liquid(env_id)
                results.extend(liquid_results)
            except Exception as e:
                logger.warning(f"Liquid retrieval failed: {e}")
        
        # 3. Ice layer (semantic/crystallized)
        if not layers or "ice" in layers:
            try:
                ice_results = await self.vector_repo.search(query, env_id, top_k=5)
                results.extend(ice_results)
            except Exception as e:
                logger.warning(f"Ice retrieval failed: {e}")
        
        # 4. Snowflakes (domain-specific)
        if pack_ids and (not layers or "snowflakes" in layers):
            try:
                snowflake_results = await self.phase_service.get_snowflakes(
                    env_id, pack_ids
                )
                results.extend(snowflake_results)
            except Exception as e:
                logger.warning(f"Snowflake retrieval failed: {e}")
        
        return self._deduplicate_and_score(results)

    def _deduplicate_and_score(self, results: List[Dict]) -> List[Dict]:
        """Deduplicate results and add relevance scores."""
        seen = set()
        unique_results = []
        for r in results:
            key = r.get('content', '') or r.get('text', '') or r.get('id', '')
            if key and key not in seen:
                seen.add(key)
                r['relevance_score'] = 1.0 - (len(seen) * 0.01)
                unique_results.append(r)
        return sorted(unique_results, key=lambda x: x.get('relevance_score', 0), reverse=True)