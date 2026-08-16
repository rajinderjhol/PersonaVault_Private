"""
Pattern Compression Service
Compresses patterns without losing intelligence.
"""
from typing import Dict, List, Any

class PatternCompressor:
    """
    Compresses learned patterns to reduce memory footprint.
    """
    
    def __init__(self, max_patterns=50):
        self.max_patterns = max_patterns
    
    def compress_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Compress patterns by keeping only the most valuable ones.
        """
        # Sort by weight and relevance
        sorted_patterns = sorted(
            patterns,
            key=lambda p: p.get("weight", 0) * p.get("confidence", 0.5),
            reverse=True
        )
        
        # Keep only top patterns
        compressed = sorted_patterns[:self.max_patterns]
        
        return compressed
    
    def deduplicate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or near-duplicate patterns.
        """
        seen = set()
        unique = []
        for p in patterns:
            key = p.get("trigger", "")[:50]
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return unique
    
    def merge_similar_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Merge similar patterns to reduce count.
        """
        # Group by type
        groups = {}
        for p in patterns:
            p_type = p.get("type", "unknown")
            if p_type not in groups:
                groups[p_type] = []
            groups[p_type].append(p)
        
        # Merge each group
        merged = []
        for p_type, group in groups.items():
            if len(group) > 1:
                # Merge by averaging weights
                avg_weight = sum(p.get("weight", 0) for p in group) / len(group)
                merged.append({
                    "type": p_type,
                    "trigger": f"{p_type}_merged",
                    "weight": avg_weight,
                    "confidence": avg_weight,
                    "is_merged": True,
                    "original_count": len(group)
                })
            else:
                merged.append(group[0])
        
        return merged
    
    def get_compression_stats(self, original: List[Dict], compressed: List[Dict]) -> Dict:
        """
        Get compression statistics.
        """
        return {
            "original_count": len(original),
            "compressed_count": len(compressed),
            "compression_ratio": len(compressed) / len(original) if original else 0,
            "space_saved": (len(original) - len(compressed)) / len(original) if original else 0
        }
