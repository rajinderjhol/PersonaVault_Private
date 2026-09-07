import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CrystallizationService:
    """Service for managing crystallized patterns (ICE memory layer)"""
    
    def __init__(self):
        self.patterns = []
        logger.info("CrystallizationService initialized")
    
    async def get_patterns(self, query: str = None, limit: int = 10) -> List[Dict]:
        """
        Get crystallized patterns from the ICE layer.
        """
        try:
            # Return sample patterns if no real data
            if not self.patterns:
                # Sample patterns for testing
                sample_patterns = [
                    {
                        "id": "pat_001",
                        "name": "Security Policy Approval",
                        "description": "Standard approval flow for security policies",
                        "confidence": 0.95,
                        "created_at": datetime.now().isoformat(),
                        "category": "security"
                    },
                    {
                        "id": "pat_002", 
                        "name": "Vendor Payment Validation",
                        "description": "Validates vendor payment requests against fraud rules",
                        "confidence": 0.92,
                        "created_at": datetime.now().isoformat(),
                        "category": "procurement"
                    },
                    {
                        "id": "pat_003",
                        "name": "Access Control Review",
                        "description": "Reviews access requests against compliance policies",
                        "confidence": 0.88,
                        "created_at": datetime.now().isoformat(),
                        "category": "compliance"
                    },
                    {
                        "id": "pat_004",
                        "name": "Contract Review Pattern",
                        "description": "Standard contract review and approval workflow",
                        "confidence": 0.90,
                        "created_at": datetime.now().isoformat(),
                        "category": "legal"
                    }
                ]
                
                # If query is provided, filter patterns
                if query:
                    query_lower = query.lower()
                    filtered = [
                        p for p in sample_patterns 
                        if query_lower in p["name"].lower() or 
                           query_lower in p["description"].lower() or
                           query_lower in p.get("category", "").lower()
                    ]
                    return filtered[:limit]
                
                return sample_patterns[:limit]
            
            # Return stored patterns
            patterns = self.patterns
            if query:
                query_lower = query.lower()
                patterns = [
                    p for p in patterns 
                    if query_lower in p.get("name", "").lower() or 
                       query_lower in p.get("description", "").lower()
                ]
            
            return patterns[:limit]
            
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return []
    
    async def search_patterns(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for patterns by query."""
        return await self.get_patterns(query, limit)
    
    async def get_recent_patterns(self, limit: int = 10) -> List[Dict]:
        """Get recent patterns."""
        return await self.get_patterns(limit=limit)
    
    async def create_pattern(self, data: Dict) -> Dict:
        """Create a new crystallized pattern."""
        pattern = {
            "id": f"pat_{len(self.patterns) + 1:04d}",
            "created_at": datetime.now().isoformat(),
            **data
        }
        self.patterns.append(pattern)
        logger.info(f"Created new pattern: {pattern['id']}")
        return pattern
    
    async def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Get a specific pattern by ID."""
        for pattern in self.patterns:
            if pattern.get("id") == pattern_id:
                return pattern
        return None
    
    async def update_pattern(self, pattern_id: str, data: Dict) -> Optional[Dict]:
        """Update an existing pattern."""
        for i, pattern in enumerate(self.patterns):
            if pattern.get("id") == pattern_id:
                self.patterns[i].update(data)
                self.patterns[i]["updated_at"] = datetime.now().isoformat()
                return self.patterns[i]
        return None
    
    async def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        for i, pattern in enumerate(self.patterns):
            if pattern.get("id") == pattern_id:
                del self.patterns[i]
                return True
        return False
