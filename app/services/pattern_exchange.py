"""
Phase 10.5: Pattern Export/Import
Share intelligence across PersonaVault instances.
"""
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.models import SemanticPattern
from app.services.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

@dataclass
class PatternPackage:
    """Package of patterns for export/import."""
    version: str = "1.0"
    exported_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "PersonaVault"
    patterns: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "version": self.version,
            "exported_at": self.exported_at,
            "source": self.source,
            "patterns": self.patterns,
            "metadata": self.metadata,
            "signature": self.signature
        }, indent=2)
    
    @classmethod
    def from_json(cls, data: str) -> 'PatternPackage':
        """Create from JSON string."""
        parsed = json.loads(data)
        package = cls(
            version=parsed.get("version", "1.0"),
            exported_at=parsed.get("exported_at"),
            source=parsed.get("source", "PersonaVault"),
            patterns=parsed.get("patterns", []),
            metadata=parsed.get("metadata", {})
        )
        package.signature = parsed.get("signature")
        return package
    
    def generate_signature(self, secret: str) -> str:
        """Generate a signature for the package."""
        content = f"{self.version}:{self.exported_at}:{self.source}:{json.dumps(self.patterns)}"
        return hashlib.sha256(f"{content}{secret}".encode()).hexdigest()
    
    def verify_signature(self, secret: str) -> bool:
        """Verify the package signature."""
        if not self.signature:
            return False
        expected = self.generate_signature(secret)
        return self.signature == expected


class PatternExporter:
    """
    Export patterns for sharing across instances.
    """
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
    
    async def export_patterns(
        self,
        pattern_ids: Optional[List[int]] = None,
        domain: Optional[str] = None,
        min_weight: float = 0.0,
        include_metadata: bool = True
    ) -> PatternPackage:
        """
        Export patterns matching criteria.
        
        Args:
            pattern_ids: Specific pattern IDs to export (None = all)
            domain: Filter by domain
            min_weight: Minimum weight threshold
            include_metadata: Include pattern metadata
        
        Returns:
            PatternPackage with exported patterns
        """
        patterns = await self.semantic_memory.get_patterns()
        
        # Filter patterns
        filtered = []
        for p in patterns:
            # Filter by IDs
            if pattern_ids and p.id not in pattern_ids:
                continue
            
            # Filter by weight
            if p.weight < min_weight:
                continue
            
            # Filter by domain (if specified)
            if domain:
                p_domain = p.pattern_type or "general"
                if domain not in p_domain and p_domain != domain:
                    continue
            
            # Convert to dict
            pattern_data = {
                "id": p.id,
                "pattern_type": p.pattern_type,
                "trigger": p.trigger,
                "correction": p.correction,
                "weight": p.weight,
                "success_count": p.success_count,
                "occurrence_count": p.occurrence_count,
                "is_active": p.is_active,
            }
            
            if include_metadata:
                pattern_data["created_at"] = p.created_at.isoformat() if p.created_at else None
                pattern_data["updated_at"] = p.updated_at.isoformat() if p.updated_at else None
                pattern_data["domain"] = p.pattern_type or "general"
                if hasattr(p, 'extra_data') and p.extra_data:
                    pattern_data["extra_data"] = p.extra_data
            
            filtered.append(pattern_data)
        
        # Create package
        package = PatternPackage(
            patterns=filtered,
            metadata={
                "export_count": len(filtered),
                "exported_by": "admin",
                "format_version": "1.0",
                "filter_criteria": {
                    "min_weight": min_weight,
                    "domain": domain
                }
            }
        )
        
        logger.info(f"📦 Exported {len(filtered)} patterns")
        return package


class PatternImporter:
    """
    Import patterns from other instances.
    """
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
        self._stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    async def import_patterns(
        self,
        package: PatternPackage,
        merge: bool = True,
        validate: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Import patterns from a package.
        
        Args:
            package: The pattern package to import
            merge: Merge with existing patterns (vs replace)
            validate: Validate patterns before import
            dry_run: Simulate import without saving
        
        Returns:
            Dict with import results
        """
        self._stats = {"imported": 0, "skipped": 0, "errors": 0}
        results = []
        
        # Validate package
        if validate:
            is_valid, error = await self._validate_package(package)
            if not is_valid:
                return {
                    "success": False,
                    "error": error,
                    "stats": self._stats
                }
        
        # Get existing patterns (for merge)
        existing_patterns = await self.semantic_memory.get_patterns() if merge else []
        existing_triggers = {p.trigger for p in existing_patterns}
        
        for pattern_data in package.patterns:
            try:
                # Check if pattern already exists (by trigger)
                trigger = pattern_data.get("trigger", "")
                if merge and trigger in existing_triggers:
                    # Skip duplicate patterns
                    self._stats["skipped"] += 1
                    results.append({
                        "trigger": trigger,
                        "status": "skipped",
                        "reason": "Pattern already exists"
                    })
                    continue
                
                # Validate pattern
                if validate and not await self._validate_pattern(pattern_data):
                    self._stats["errors"] += 1
                    results.append({
                        "trigger": trigger,
                        "status": "error",
                        "reason": "Validation failed"
                    })
                    continue
                
                if not dry_run:
                    # Create and save pattern
                    pattern = SemanticPattern(
                        pattern_type=pattern_data.get("pattern_type", "general"),
                        trigger=trigger,
                        correction=pattern_data.get("correction", ""),
                        weight=pattern_data.get("weight", 0.7),
                        success_count=pattern_data.get("success_count", 0),
                        occurrence_count=pattern_data.get("occurrence_count", 1),
                        is_active=pattern_data.get("is_active", True),
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    # Add extra data
                    if "extra_data" in pattern_data:
                        pattern.extra_data = pattern_data["extra_data"]
                    
                    await self.semantic_memory.add_pattern(pattern)
                    self._stats["imported"] += 1
                    results.append({
                        "trigger": trigger,
                        "status": "imported",
                        "weight": pattern.weight
                    })
                else:
                    self._stats["imported"] += 1
                    results.append({
                        "trigger": trigger,
                        "status": "dry_run",
                        "weight": pattern_data.get("weight", 0.7)
                    })
                
            except Exception as e:
                self._stats["errors"] += 1
                results.append({
                    "trigger": pattern_data.get("trigger", "unknown"),
                    "status": "error",
                    "reason": str(e)
                })
        
        return {
            "success": True,
            "stats": self._stats,
            "results": results,
            "dry_run": dry_run
        }
    
    async def _validate_package(self, package: PatternPackage) -> tuple:
        """Validate the pattern package."""
        if not package.patterns:
            return False, "Package contains no patterns"
        
        for p in package.patterns:
            if not p.get("trigger"):
                return False, "Pattern missing trigger"
            if not p.get("pattern_type"):
                return False, "Pattern missing type"
        
        return True, "Valid"
    
    async def _validate_pattern(self, pattern_data: Dict) -> bool:
        """Validate a single pattern."""
        required = ["trigger", "pattern_type"]
        for field in required:
            if not pattern_data.get(field):
                return False
        
        # Validate weight range
        weight = pattern_data.get("weight", 0.5)
        if not (0 <= weight <= 1):
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, int]:
        """Get import statistics."""
        return self._stats.copy()
