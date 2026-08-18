"""
Phase 10.3: Cross-Domain Pattern Transfer
Transfers learnings across domains.
"""
import logging
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models import SemanticPattern
from app.services.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

@dataclass
class DomainMapping:
    """Mapping between domains for pattern transfer."""
    source_domain: str
    target_domain: str
    similarity_score: float
    transfer_rules: Dict[str, str] = field(default_factory=dict)


class DomainTransfer:
    """
    Transfers patterns across domains.
    Enables cross-domain learning and intelligence sharing.
    """
    
    # Domain similarity matrix
    DOMAIN_SIMILARITY = {
        ("security", "compliance"): 0.85,
        ("security", "legal"): 0.75,
        ("security", "procurement"): 0.60,
        ("compliance", "legal"): 0.80,
        ("compliance", "insurance"): 0.70,
        ("contract", "legal"): 0.90,
        ("contract", "procurement"): 0.75,
        ("procurement", "insurance"): 0.65,
        ("robotics", "security"): 0.60,
        ("robotics", "health"): 0.80,
        ("health", "insurance"): 0.70,
        ("health", "compliance"): 0.75,
    }
    
    # Domain-specific mapping rules
    TRANSFER_RULES = {
        ("security", "compliance"): {
            "security_incident": "compliance_violation",
            "threat": "risk",
            "mitigation": "remediation"
        },
        ("contract", "legal"): {
            "vendor": "party",
            "payment": "consideration",
            "term": "provision"
        },
        ("procurement", "contract"): {
            "supplier": "vendor",
            "purchase_order": "agreement",
            "delivery": "performance"
        }
    }
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
        self._transfer_cache: Dict[str, List[SemanticPattern]] = {}
    
    async def transfer_pattern(
        self,
        pattern: SemanticPattern,
        source_domain: str,
        target_domain: str
    ) -> Optional[SemanticPattern]:
        """
        Transfer a pattern from source domain to target domain.
        
        Args:
            pattern: The pattern to transfer
            source_domain: Source domain name
            target_domain: Target domain name
        
        Returns:
            Transferred pattern or None if not applicable
        """
        # Check if domains are similar enough
        similarity = self._get_similarity(source_domain, target_domain)
        if similarity < 0.5:
            logger.debug(f"Domains too dissimilar: {source_domain} → {target_domain} (similarity: {similarity:.2f})")
            return None
        
        # Get transfer rules
        rules = self._get_transfer_rules(source_domain, target_domain)
        
        # Apply domain mapping to pattern
        mapped_trigger = self._apply_rules(pattern.trigger, rules)
        mapped_correction = self._apply_rules(pattern.correction, rules)
        
        # Create transferred pattern
        transferred = SemanticPattern(
            pattern_type=pattern.pattern_type,
            trigger=f"[{target_domain}] {mapped_trigger[:90]}",
            correction=mapped_correction,
            success_count=0,  # Reset for new domain
            weight=pattern.weight * 0.7,  # Slightly lower weight for transferred patterns
            is_active=True,
            occurrence_count=1,
            created_at=datetime.now(timezone.utc)
        )
        
        # Add metadata about transfer
        transferred.extra_data = {
            "source_domain": source_domain,
            "target_domain": target_domain,
            "original_pattern_id": pattern.id,
            "similarity_score": similarity,
            "transferred_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"🔄 Transferred pattern {pattern.id} from {source_domain} to {target_domain}")
        return transferred
    
    async def transfer_domain(
        self,
        source_domain: str,
        target_domain: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Transfer all applicable patterns from source to target domain.
        
        Returns:
            Dict with transfer results
        """
        # Get patterns from source domain
        patterns = await self.semantic_memory.get_all_patterns()
        source_patterns = [
            p for p in patterns
            if p.pattern_type == source_domain or source_domain in (p.trigger or "")
        ]
        
        if not source_patterns:
            return {
                "source_domain": source_domain,
                "target_domain": target_domain,
                "transferred": 0,
                "patterns": []
            }
        
        # Transfer patterns
        transferred = []
        for pattern in source_patterns[:limit]:
            result = await self.transfer_pattern(pattern, source_domain, target_domain)
            if result:
                # Save to semantic memory
                await self.semantic_memory.add_pattern(result)
                transferred.append({
                    "original_id": pattern.id,
                    "new_id": result.id,
                    "trigger": result.trigger[:50],
                    "weight": result.weight
                })
        
        return {
            "source_domain": source_domain,
            "target_domain": target_domain,
            "transferred": len(transferred),
            "patterns": transferred
        }
    
    async def transfer_all_domains(self) -> Dict[str, Any]:
        """
        Transfer patterns across all domain pairs.
        """
        results = {}
        domains = set()
        
        # Collect all domains
        for (src, tgt) in self.DOMAIN_SIMILARITY.keys():
            domains.add(src)
            domains.add(tgt)
        
        # Transfer between all domain pairs
        for src in domains:
            for tgt in domains:
                if src == tgt:
                    continue
                if self._get_similarity(src, tgt) < 0.5:
                    continue
                
                key = f"{src}→{tgt}"
                results[key] = await self.transfer_domain(src, tgt)
        
        return {
            "total_transfers": sum(r["transferred"] for r in results.values()),
            "domain_pairs": len(results),
            "results": results
        }
    
    def _get_similarity(self, domain1: str, domain2: str) -> float:
        """Get similarity score between two domains."""
        # Check exact match
        if (domain1, domain2) in self.DOMAIN_SIMILARITY:
            return self.DOMAIN_SIMILARITY[(domain1, domain2)]
        if (domain2, domain1) in self.DOMAIN_SIMILARITY:
            return self.DOMAIN_SIMILARITY[(domain2, domain1)]
        
        # Check partial matches
        if domain1 in domain2 or domain2 in domain1:
            return 0.5
        
        return 0.0
    
    def _get_transfer_rules(self, source_domain: str, target_domain: str) -> Dict[str, str]:
        """Get transfer rules between two domains."""
        # Check exact match
        if (source_domain, target_domain) in self.TRANSFER_RULES:
            return self.TRANSFER_RULES[(source_domain, target_domain)]
        if (target_domain, source_domain) in self.TRANSFER_RULES:
            return self.TRANSFER_RULES[(target_domain, source_domain)]
        
        return {}
    
    def _apply_rules(self, text: str, rules: Dict[str, str]) -> str:
        """Apply mapping rules to text."""
        if not rules or not text:
            return text
        
        result = text
        for from_word, to_word in rules.items():
            result = result.replace(from_word, to_word)
        
        return result
    
    async def get_domain_stats(self) -> Dict[str, Any]:
        """
        Get domain transfer statistics.
        """
        patterns = await self.semantic_memory.get_all_patterns()
        
        # Count patterns by domain
        domain_counts = {}
        transferred_count = 0
        
        for p in patterns:
            if hasattr(p, 'extra_data') and p.extra_data and 'source_domain' in p.extra_data:
                transferred_count += 1
                # TODO: Track domain counts from transferred patterns
        
        return {
            "total_patterns": len(patterns),
            "transferred_patterns": transferred_count,
            "domains": domain_counts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
