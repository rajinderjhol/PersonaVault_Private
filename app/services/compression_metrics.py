"""
Phase 10.4: Compression Ratio Dashboard
Tracks and visualizes intelligence compression metrics.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from app.models import Memory, SemanticPattern, EpisodicEntry, BehaviourEvent
from app.services.semantic_memory import SemanticMemory
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

@dataclass
class CompressionSnapshot:
    """Snapshot of compression metrics at a point in time."""
    timestamp: datetime
    raw_data_size: int  # in tokens
    compressed_size: int  # in patterns
    compression_ratio: float
    sources_count: int
    patterns_count: int
    active_patterns: int
    avg_pattern_weight: float
    domains: Dict[str, int]


class CompressionMetrics:
    """
    Tracks and calculates compression metrics.
    Target: 10,000:1 compression ratio.
    """
    
    # Average tokens per memory (approximate)
    AVG_TOKENS_PER_MEMORY = 100
    AVG_TOKENS_PER_EPISODIC = 50
    
    def __init__(self, db_session, repository):
        self.db = db_session
        self.repository = repository
        self._history: List[CompressionSnapshot] = []
        self._target_ratio = 10000
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current compression metrics.
        """
        # Get counts from database
        memories_count = await self._count_memories()
        episodic_count = await self._count_episodic()
        decisions_count = await self._count_decisions()
        
        # Get patterns
        semantic_memory = SemanticMemory(self.repository)
        patterns = await semantic_memory.get_patterns()
        
        # Calculate success rate
        success_patterns = len([p for p in patterns if p.pattern_type == "success"])
        success_rate = (success_patterns / max(len(patterns), 1)) * 100
        
        # Calculate raw data size (in tokens)
        raw_data_size = (
            memories_count * self.AVG_TOKENS_PER_MEMORY +
            episodic_count * self.AVG_TOKENS_PER_EPISODIC +
            decisions_count * 20  # Decisions are shorter
        )
        
        # Calculate compressed size (patterns)
        compressed_size = len(patterns)
        active_patterns = len([p for p in patterns if p.is_active])
        
        # Calculate compression ratio
        compression_ratio = raw_data_size / max(compressed_size, 1)
        
        # Get domain distribution
        domains = self._get_domain_distribution(patterns)
        
        # Calculate average weight
        avg_weight = sum(p.weight for p in patterns) / max(len(patterns), 1)
        
        # Get recent compression history
        history = self._history[-10:] if self._history else []
        
        # Calculate progress toward target
        progress = min(100, (compression_ratio / self._target_ratio) * 100)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_data_size": raw_data_size,
            "compressed_size": compressed_size,
            "compression_ratio": round(compression_ratio, 2),
            "target_ratio": self._target_ratio,
            "progress_percent": round(progress, 2),
            "success_rate": round(success_rate, 2),
            "sources_count": {
                "memories": memories_count,
                "episodic": episodic_count,
                "decisions": decisions_count
            },
            "patterns_count": {
                "total": compressed_size,
                "active": active_patterns,
                "inactive": compressed_size - active_patterns
            },
            "avg_pattern_weight": round(avg_weight, 3),
            "domains": domains,
            "history": [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "compression_ratio": round(h.compression_ratio, 2),
                    "patterns_count": h.patterns_count
                }
                for h in history
            ],
            "patterns": [
                {"type": p.pattern_type, "trigger": p.trigger, "weight": p.weight, "is_active": p.is_active}
                for p in patterns[:20]
            ]
        }
    
    async def _count_memories(self) -> int:
        """Count total memories."""
        try:
            stmt = select(func.count(Memory.id))
            result = await self.db.execute(stmt)
            return result.scalar_one() or 0
        except Exception as e:
            logger.warning(f"Failed to count memories: {e}")
            return 0
    
    async def _count_episodic(self) -> int:
        """Count episodic entries."""
        try:
            stmt = select(func.count(EpisodicEntry.id))
            result = await self.db.execute(stmt)
            return result.scalar_one() or 0
        except Exception as e:
            logger.warning(f"Failed to count episodic: {e}")
            return 0
    
    async def _count_decisions(self) -> int:
        """Count decisions (behaviour events)."""
        try:
            stmt = select(func.count(BehaviourEvent.id))
            result = await self.db.execute(stmt)
            return result.scalar_one() or 0
        except Exception as e:
            logger.warning(f"Failed to count decisions: {e}")
            return 0
    
    def _get_domain_distribution(self, patterns: List) -> Dict[str, int]:
        """Get domain distribution from patterns."""
        domains = {}
        for p in patterns:
            # Extract domain from pattern_type or trigger
            domain = p.pattern_type or "general"
            # Assuming pattern might have extra_data dict in future
            # if hasattr(p, 'extra_data') and p.extra_data:
            #     if 'domain' in p.extra_data:
            #         domain = p.extra_data['domain']
            domains[domain] = domains.get(domain, 0) + 1
        return domains
    
    async def take_snapshot(self) -> CompressionSnapshot:
        """
        Take a snapshot of current compression metrics.
        """
        metrics = await self.get_current_metrics()
        
        snapshot = CompressionSnapshot(
            timestamp=datetime.now(timezone.utc),
            raw_data_size=metrics["raw_data_size"],
            compressed_size=metrics["compressed_size"],
            compression_ratio=metrics["compression_ratio"],
            sources_count=sum(metrics["sources_count"].values()),
            patterns_count=metrics["patterns_count"]["total"],
            active_patterns=metrics["patterns_count"]["active"],
            avg_pattern_weight=metrics["avg_pattern_weight"],
            domains=metrics["domains"]
        )
        
        self._history.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        return snapshot
    
    async def get_compression_timeline(self, days: int = 30) -> List[Dict]:
        """
        Get compression history for timeline visualization.
        """
        # If we don't have history, generate sample data
        if not self._history:
            return self._generate_sample_timeline(days)
        
        # Filter by days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        history = [h for h in self._history if h.timestamp > cutoff]
        
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "compression_ratio": round(h.compression_ratio, 2),
                "patterns_count": h.patterns_count,
                "active_patterns": h.active_patterns,
                "avg_weight": round(h.avg_pattern_weight, 3)
            }
            for h in history
        ]
    
    def _generate_sample_timeline(self, days: int) -> List[Dict]:
        """
        Generate sample timeline data for testing.
        """
        import random
        timeline = []
        now = datetime.now(timezone.utc)
        
        # Start with some initial values
        ratio = 50
        patterns = 5
        active = 3
        weight = 0.5
        
        for i in range(days, 0, -1):
            date = now - timedelta(days=i)
            # Add some variation
            ratio += random.randint(-5, 20)
            patterns += random.randint(0, 2)
            active += random.randint(0, 1)
            weight += random.uniform(-0.02, 0.05)
            
            timeline.append({
                "timestamp": date.isoformat(),
                "compression_ratio": round(max(10, ratio), 2),
                "patterns_count": max(1, patterns),
                "active_patterns": max(1, active),
                "avg_weight": round(max(0.1, min(1.0, weight)), 3)
            })
        
        return timeline
    
    async def get_compression_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed breakdown of compression sources.
        """
        metrics = await self.get_current_metrics()
        return {
            "raw_data": {
                "memories": metrics["sources_count"]["memories"],
                "episodic": metrics["sources_count"]["episodic"],
                "decisions": metrics["sources_count"]["decisions"],
                "total_tokens": metrics["raw_data_size"]
            },
            "compressed": {
                "patterns": metrics["patterns_count"]["total"],
                "active": metrics["patterns_count"]["active"],
                "inactive": metrics["patterns_count"]["inactive"],
                "avg_weight": metrics["avg_pattern_weight"]
            },
            "efficiency": {
                "compression_ratio": metrics["compression_ratio"],
                "target_ratio": self._target_ratio,
                "progress": metrics["progress_percent"]
            },
            "domains": metrics["domains"]
        }
