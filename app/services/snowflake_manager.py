"""
Snowflake Manager
Generates domain-specific intelligence (Snowflakes) from crystallized Ice patterns
and Behavior Pack domain specializations.
"""
from typing import Dict, Any
from datetime import datetime
from app.services.memory_thermodynamics import MemoryPhase

class SnowflakeManager:
    def __init__(self, pack_executor):
        self.pack_executor = pack_executor
    
    def get_domain_specializations(self) -> Dict[str, Any]:
        """Extract domain specializations from loaded behavior packs."""
        specializations = {}
        # Get all loaded packs from the executor
        # Assuming executor stores packs in a way that allows access
        for pack_name, pack_instance in self.pack_executor.loaded_packs.items():
            template = pack_instance.get_snowflake_template()
            domain = template.get('domain', pack_name)
            specializations[domain] = template
        return specializations
    
    async def create_snowflake(self, base_pattern: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Create a snowflake from a base pattern using pack specialization."""
        # 1. Get specializations
        specs = self.get_domain_specializations()
        pack_spec = specs.get(domain)
        
        if not pack_spec:
            raise ValueError(f"No pack specialization found for domain: {domain}")
        
        # 2. Create the snowflake
        snowflake = {
            "id": f"{base_pattern['id']}_{domain}",
            "parent_id": base_pattern["id"],
            "phase": MemoryPhase.SNOWFLAKE.value,
            "domain": domain,
            "base_pattern": base_pattern,
            "specialization": pack_spec,
            "created_at": datetime.utcnow().isoformat()
        }
        return snowflake
