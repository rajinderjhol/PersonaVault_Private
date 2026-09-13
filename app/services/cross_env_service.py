import logging
from typing import List, Dict, Any, Optional
from app.swarm.core.privacy import privacy_abstraction_agent
from app.api.v2.services.crystallization_service import crystallization_service
from app.api.v2.services.environment_service import environment_service

logger = logging.getLogger(__name__)

class CrossEnvironmentService:
    """
    V3 Cross-Environment Service: Facilitates secure intelligence transfer 
    between isolated environments using privacy abstraction.
    """
    
    def __init__(self, agent=None, crystallization_svc=None):
        self.agent = agent or privacy_abstraction_agent
        self.crystallization_svc = crystallization_svc or crystallization_service

    async def transfer_intelligence(self, source_env_id: str, target_env_id: str) -> Dict[str, Any]:
        """
        Transfer abstracted intelligence from source to target.
        """
        logger.info(f"🔄 Securely transferring intelligence: {source_env_id} → {target_env_id}")
        
        # 1. Fetch patterns from source
        source_patterns = await self.crystallization_svc.get_patterns(source_env_id)
        if not source_patterns:
            return {"status": "skipped", "reason": "No patterns in source environment"}

        # 2. Abstract and Anonymize
        abstracted_patterns = []
        for p in source_patterns:
            abs_p = await self.agent.abstract_pattern(p)
            if abs_p.get("privacy_confidence", 0) > 0.9: # Strict privacy threshold
                abstracted_patterns.append(abs_p)

        # 3. Save to target
        target_env = await environment_service.get_environment(target_env_id)
        if not target_env:
            return {"status": "error", "reason": f"Target environment {target_env_id} not found"}

        transferred_ids = []
        for ap in abstracted_patterns:
            try:
                mp_data = {
                    "title": f"SHARED: {ap['abstract_title']}",
                    "content": ap["abstract_content"],
                    "tags": ["cross-env-transfer", "anonymized"] + ap.get("universal_anchors", []),
                    "metadata": {
                        "type": "crystallized_pattern",
                        "is_shared": True,
                        "source_env_hash": hash(source_env_id),
                        "privacy_confidence": ap.get("privacy_confidence")
                    }
                }
                mp_id = await self.crystallization_svc.crystallize_pattern(target_env, mp_data)
                transferred_ids.append(mp_id)
            except Exception as e:
                logger.error(f"Failed to save transferred pattern: {e}")

        return {
            "status": "success",
            "patterns_abstracted": len(abstracted_patterns),
            "patterns_transferred": len(transferred_ids),
            "transferred_ids": transferred_ids
        }

cross_env_service = CrossEnvironmentService()
