import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.marketplace import (
    MarketplacePack, PackMetadata, PackStatistics, 
    PackVersion, PackStatus, PackCategory
)

logger = logging.getLogger(__name__)


class MarketplaceRegistry:
    """Registry for available packs in the marketplace."""
    
    def __init__(self):
        self.registry_path = Path("data/marketplace_registry.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.packs = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    self.packs = data.get("packs", {})
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self.packs = {}
    
    def _save_registry(self):
        """Save registry to disk."""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump({"packs": self.packs}, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_pack(
        self,
        pack_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Register a pack in the marketplace."""
        
        # Create pack entry
        pack_entry = {
            "id": pack_id,
            "metadata": metadata,
            "statistics": {
                "download_count": 0,
                "rating_avg": 0.0,
                "rating_count": 0,
                "use_count": 0,
                "pattern_count": 0,
                "confidence_avg": 0.0
            },
            "versions": [
                {
                    "version": metadata.get("version", "1.0.0"),
                    "released_at": datetime.now().isoformat(),
                    "changelog": metadata.get("changelog", "Initial release"),
                    "download_url": f"/api/v1/marketplace/packs/{pack_id}/download",
                    "size_bytes": 0,
                    "min_platform_version": metadata.get("min_platform_version", "2.0.0"),
                    "is_latest": True,
                    "is_deprecated": False
                }
            ],
            "reviews": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.packs[pack_id] = pack_entry
        self._save_registry()
        
        logger.info(f"Registered pack: {pack_id}")
        
        return pack_entry
    
    def get_pack(self, pack_id: str) -> Optional[Dict[str, Any]]:
        """Get a pack by ID."""
        return self.packs.get(pack_id)
    
    def list_packs(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List packs with filtering."""
        packs = list(self.packs.values())
        
        # Filter by category
        if category:
            packs = [
                p for p in packs 
                if p.get("metadata", {}).get("category") == category
            ]
        
        # Filter by search
        if search:
            search_lower = search.lower()
            packs = [
                p for p in packs
                if search_lower in p.get("metadata", {}).get("name", "").lower()
                or search_lower in p.get("metadata", {}).get("description", "").lower()
            ]
        
        # Filter by min confidence
        if min_confidence > 0:
            packs = [
                p for p in packs
                if p.get("statistics", {}).get("confidence_avg", 0) >= min_confidence
            ]
        
        # Sort by download count
        packs.sort(
            key=lambda x: x.get("statistics", {}).get("download_count", 0),
            reverse=True
        )
        
        # Paginate
        total = len(packs)
        packs = packs[offset:offset + limit]
        
        return {
            "packs": packs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    def update_statistics(
        self,
        pack_id: str,
        statistics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update pack statistics."""
        if pack_id not in self.packs:
            return None
        
        pack = self.packs[pack_id]
        for key, value in statistics.items():
            if key in pack.get("statistics", {}):
                pack["statistics"][key] = value
        
        pack["updated_at"] = datetime.now().isoformat()
        self._save_registry()
        
        return pack
    
    def add_review(
        self,
        pack_id: str,
        rating: int,
        comment: str,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Add a review to a pack."""
        if pack_id not in self.packs:
            return None
        
        pack = self.packs[pack_id]
        
        review = {
            "rating": rating,
            "comment": comment,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        
        pack["reviews"].append(review)
        
        # Update statistics
        stats = pack.get("statistics", {})
        ratings = [r.get("rating", 0) for r in pack["reviews"]]
        stats["rating_avg"] = sum(ratings) / len(ratings) if ratings else 0
        stats["rating_count"] = len(ratings)
        
        self._save_registry()
        
        return review
