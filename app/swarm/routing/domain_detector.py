import logging
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)

@dataclass
class DomainResult:
    """Result of domain detection."""
    domain: str
    confidence: float
    patterns: List[Dict] = field(default_factory=list)
    all_matches: List[Dict] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    detection_method: str = "keyword"

class DomainDetector:
    """Lightweight domain detector scanning multiple pack directories."""
    
    def __init__(self, packs_dir: Optional[Path] = None):
        # Scan both app/packs and root/packs
        self.pack_dirs = [packs_dir] if packs_dir else [Path("app/packs"), Path("packs")]
        self.pack_keywords: Dict[str, Set[str]] = {}
        self.pack_metadata: Dict[str, Dict] = {}
        self.pack_patterns: Dict[str, List[Dict]] = {}
        self._load_all_packs()
        
        logger.info(f"DomainDetector initialized with {len(self.pack_keywords)} domains")
        if self.pack_keywords:
            logger.info(f"Domains: {list(self.pack_keywords.keys())}")
            
    def _load_all_packs(self):
        """Load packs from all registered directories."""
        for packs_dir in self.pack_dirs:
            print(f"DEBUG: Scanning packs directory: {packs_dir}, exists: {packs_dir.exists()}")
            if not packs_dir.exists():
                logger.debug(f"Packs directory not found: {packs_dir}")
                continue
            
            # Scan for both legacy behavior_pack.yaml and new pack.yaml
            for pack_path in list(packs_dir.glob("*/behaviour_pack.yaml")) + list(packs_dir.glob("*/pack.yaml")):
                print(f"DEBUG: Found pack file: {pack_path}")
                self._load_pack_data(pack_path)
                self._load_pack_patterns(pack_path)

    def _load_pack_data(self, pack_path: Path):
        try:
            with open(pack_path, 'r') as f:
                config = yaml.safe_load(f)
            
            domain = config.get("pack", {}).get("name")
            if not domain: return
            
            keywords = set()
            description = config.get("pack", {}).get("description", "")
            keywords.update(self._extract_keywords(description))
            
            # Extract keywords from policies
            policies_dir = pack_path.parent / "policies"
            if policies_dir.exists():
                for p_file in policies_dir.glob("*.yaml"):
                    with open(p_file, 'r') as pf:
                        keywords.update(self._extract_keywords(str(yaml.safe_load(pf))))
            
            keywords.add(domain.lower())
            keywords.discard("")
            self.pack_keywords[domain] = keywords
            logger.info(f"Loaded {domain} from {pack_path}")
        except Exception as e:
            logger.error(f"Failed to load pack {pack_path}: {e}")

    def _load_pack_patterns(self, pack_path: Path):
        domain = None
        try:
            with open(pack_path, 'r') as f:
                domain = yaml.safe_load(f).get("pack", {}).get("name")
        except: return
        
        if not domain: return
        
        patterns = []
        patterns_dir = pack_path.parent / "crystallized"
        if patterns_dir.exists():
            for p_file in patterns_dir.glob("*.json"):
                try:
                    with open(p_file, 'r') as pf:
                        patterns.append(json.load(pf))
                except: pass
        self.pack_patterns[domain] = patterns

    def _extract_keywords(self, text: str) -> Set[str]:
        if not text: return set()
        words = re.findall(r'\b\w+\b', text.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'nor', 'on', 'at', 'to', 'by', 'of', 'in', 'with', 'without', 'from', 'about', 'as', 'so', 'if', 'then', 'when', 'where', 'what', 'which', 'who', 'whom', 'whose', 'that', 'this', 'these', 'those', 'have', 'has', 'had', 'been', 'being', 'is', 'am', 'are', 'was', 'were', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'it', 'its', 'they', 'them', 'their', 'she', 'he', 'her', 'him', 'his', 'our', 'my', 'your', 'me', 'us'}
        return set(w for w in words if len(w) > 2 and w not in stopwords)

    def get_domain_stats(self) -> Dict[str, Any]:
        return {
            "total_domains": len(self.pack_keywords),
            "domains": [
                {
                    "name": domain,
                    "keyword_count": len(keywords),
                    "pattern_count": len(self.pack_patterns.get(domain, [])),
                    "version": self.pack_metadata.get(domain, {}).get("version", "unknown")
                }
                for domain, keywords in self.pack_keywords.items()
            ]
        }

    async def detect(self, query: str, context: Optional[Dict] = None, force_domain: Optional[str] = None) -> DomainResult:
        if force_domain and force_domain in self.pack_keywords:
            return DomainResult(domain=force_domain, confidence=0.95, patterns=self.pack_patterns.get(force_domain, []))
        
        query_words = self._extract_keywords(query)
        if not query_words or not self.pack_keywords:
            return DomainResult(domain="general", confidence=0.0)
            
        domain_scores = []
        for domain, keywords in self.pack_keywords.items():
            overlap = len(query_words.intersection(keywords))
            if overlap == 0: continue
            
            confidence = min(overlap / len(query_words) * 1.5, 1.0)
            domain_scores.append({"domain": domain, "confidence": confidence})
        
        domain_scores.sort(key=lambda x: x["confidence"], reverse=True)
        if domain_scores and domain_scores[0]["confidence"] > 0.3:
            return DomainResult(domain=domain_scores[0]["domain"], confidence=domain_scores[0]["confidence"], patterns=self.pack_patterns.get(domain_scores[0]["domain"], []))
        
        return DomainResult(domain="general", confidence=0.0)
