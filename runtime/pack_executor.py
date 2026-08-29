"""
Pack Executor - Runtime execution of compiled packs
"""
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

from app.services.trace_service import TraceService, TraceStep

class PackExecutor:
    """Execute compiled behavior packs"""
    
    def __init__(self, pack_dir: str = "packs/compiled", trace_service: Optional[TraceService] = None):
        self.pack_dir = Path(pack_dir)
        self.loaded_packs: Dict[str, Any] = {}
        self.pack_metadata: Dict[str, Dict] = {}
        self.trace_service = trace_service
        
        # Auto-load all compiled packs
        self._load_all_packs()
    
    def _load_all_packs(self):
        """Load all compiled packs from directory"""
        if not self.pack_dir.exists():
            return
            
        for py_file in self.pack_dir.glob("*_pack.py"):
            pack_name = py_file.stem.replace("_pack", "")
            try:
                self.load_pack(pack_name)
            except Exception as e:
                logger.error(f"❌ Failed to load pack {pack_name}: {e}")
        
        logger.info(f"✅ Loaded {len(self.loaded_packs)} packs")
    
    def load_pack(self, pack_name: str) -> Any:
        """Load a specific compiled pack using file path to avoid import issues"""
        py_file = self.pack_dir / f"{pack_name}_pack.py"
        if not py_file.exists():
            raise FileNotFoundError(f"Pack file not found: {py_file}")
            
        try:
            # Load module from file path
            module_name = f"packs.compiled.{pack_name}_pack"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the pack class
            pack_class = None
            for attr_name in dir(module):
                if attr_name.endswith("Pack") and not attr_name.startswith("Compiled"):
                    pack_class = getattr(module, attr_name)
                    break
            
            if not pack_class:
                raise ValueError(f"No Pack class found in module {module_name}")
            
            # Instantiate the pack
            pack_instance = pack_class()
            self.loaded_packs[pack_name] = pack_instance
            
            # Store metadata
            self.pack_metadata[pack_name] = pack_instance.get_metadata()
            
            logger.info(f"✅ Loaded pack: {pack_name} v{pack_instance.metadata['version']}")
            return pack_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to load pack {pack_name}: {e}")
            raise
    
    def get_pack(self, pack_name: str) -> Any:
        """Get a loaded pack by name"""
        return self.loaded_packs.get(pack_name)
    
    def get_pack_by_domain(self, domain: str) -> List[Any]:
        """Get all packs in a domain"""
        packs = []
        for pack_name, pack in self.loaded_packs.items():
            if pack.metadata.get('domain') == domain:
                packs.append(pack)
        return packs
    
    async def process_with_pack(
        self,
        pack_name: str,
        raw_input: str,
        user_id: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process input using a specific pack"""
        pack = self.get_pack(pack_name)
        if not pack:
            raise ValueError(f"Pack not found: {pack_name}")
        
        return await pack.process(raw_input, user_id, session_id)
    
    async def process_with_best_pack(
        self,
        raw_input: str,
        user_id: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Auto-select the best pack based on input"""
        # Simple keyword-based selection
        input_lower = raw_input.lower()
        
        # Score each pack
        pack_scores = {}
        for pack_name, pack in self.loaded_packs.items():
            score = 0
            metadata = pack.metadata
            
            # Check against pack domain
            domain = metadata.get('domain', '')
            if domain and domain.lower() in input_lower:
                score += 3
            
            # Check against entities
            if hasattr(pack, 'get_supported_entities'):
                entities = pack.get_supported_entities()
                for entity_name in entities.keys():
                    if entity_name.lower() in input_lower:
                        score += 1
            
            pack_scores[pack_name] = score
        
        # Select best match
        result = None
        if pack_scores:
            best_pack = max(pack_scores, key=pack_scores.get)
            if pack_scores[best_pack] > 0:
                result = await self.process_with_pack(best_pack, raw_input, user_id, session_id)
        
        if not result:
            # No pack matched
            result = {
                "decision": {
                    "policy": "no_match",
                    "type": "observe",
                    "severity": "low",
                    "confidence": 0.0,
                    "reasoning": "No pack matched the input"
                },
                "actions": [],
                "autonomy": {
                    "level": "observe",
                    "needs_approval": False,
                    "can_execute": False
                },
                "provenance": {
                    "raw_input": raw_input,
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": {
                    "pack": "none",
                    "version": "1.0.0"
                }
            }

        # Persist trace if service available
        if self.trace_service and session_id:
            try:
                await self.trace_service.capture_step(
                    session_id=int(session_id) if isinstance(session_id, str) and session_id.isdigit() else (session_id if isinstance(session_id, int) else 1),
                    step=TraceStep.POLICY_MATCH,
                    data=result,
                    agent_id="pack_executor",
                    confidence_score=result["decision"].get("confidence", 0.0)
                )
            except Exception as e:
                logger.error(f"Failed to persist policy trace: {e}")

        return result
    
    def list_packs(self) -> List[Dict[str, Any]]:
        """List all loaded packs with metadata"""
        return [
            {
                "name": name,
                "metadata": pack.metadata
            }
            for name, pack in self.loaded_packs.items()
        ]
