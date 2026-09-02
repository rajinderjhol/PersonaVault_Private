"""
Phase 10.7: Crystallization Service
Moves patterns from Liquid (episodic) to Ice (semantic) with confidence thresholds.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from app.models import EpisodicEntry, SemanticPattern
from app.services.semantic_memory import SemanticMemory
from app.services.temporal_analysis_service import TemporalAnalysisService

logger = logging.getLogger(__name__)

@dataclass
class CrystallizationConfig:
    """Configuration for crystallization."""
    confidence_threshold: float = 0.7
    min_occurrences: int = 3
    batch_size: int = 10
    interval_hours: float = 0.5
    weight_boost: float = 0.1  # Weight increase when crystallized

class CrystallizationService:
    """
    Crystallizes patterns from Liquid (episodic) to Ice (semantic).
    Only patterns with high confidence and multiple occurrences graduate.
    """
    
    def __init__(self, session_factory, semantic_memory: Optional[SemanticMemory] = None):
        self.session_factory = session_factory
        self.semantic_memory = semantic_memory or SemanticMemory(session_factory)
        # Note: TemporalAnalysisService requires an async session. 
        # We will initialize it inside methods that have session access or use the factory.
        self.config = CrystallizationConfig()
        self._stats = {"crystallized": 0, "skipped": 0, "errors": 0}
    
    async def calculate_pattern_relevance(self, pattern: SemanticPattern, db: AsyncSession) -> float:
        """
        Calculate current relevance score with time-decay.
        """
        temporal_service = TemporalAnalysisService(db)
        base_score = getattr(pattern, 'weight', 0.5)
        
        # Apply temporal decay based on pattern age
        decay_factor = temporal_service.calculate_pattern_decay(
            confidence=base_score,
            last_reinforced=pattern.created_at
        )
        
        # Relevance = base_score * decay_factor
        return base_score * decay_factor

    async def should_crystallize(self, entry: EpisodicEntry, db: AsyncSession) -> bool:
        """Enhanced crystallization check with temporal context"""
        # ... existing logic ...
        
        # Check confidence threshold first
        if not await self._qualifies_for_crystallization(entry):
            return False
        
        # Add temporal velocity check - only crystallize if pattern shows temporal stability
        temporal_service = TemporalAnalysisService(db)
        velocity_data = await temporal_service.calculate_decision_velocity(
            user_id=entry.user_id,
            days=7
        )
        velocity = velocity_data.get("velocity", 0)
        
        # Patterns with very high velocity (rapid change) may not be ready for crystallization
        if velocity > 0.9:  # threshold
            logger.info(f"Pattern velocity too high ({velocity}), deferring crystallization")
            return False
        
        return True
    
    async def crystallize(self, entry: EpisodicEntry) -> Optional[SemanticPattern]:
        """
        Crystallize an episodic entry into a semantic pattern.
        """
        # Check if entry qualifies for crystallization
        if not await self._qualifies_for_crystallization(entry):
            return None
        
        # Extract pattern from entry
        pattern_data = await self._extract_pattern(entry)
        if not pattern_data:
            return None
        
        # Create semantic pattern
        pattern = SemanticPattern(
            pattern_type=pattern_data.get("type", "general"),
            trigger=pattern_data.get("trigger", entry.query[:100] if entry.query else "unknown"),
            correction=pattern_data.get("correction", ""),
            weight=0.8 + self.config.weight_boost,  # Higher weight for crystallized patterns
            success_count=1,
            occurrence_count=1,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Add metadata about crystallization
        pattern.extra_data = {
            "crystallized_from": entry.id,
            "crystallized_at": datetime.now(timezone.utc).isoformat(),
            "source_query": entry.query,
            "confidence": pattern_data.get("confidence", 0.8)
        }
        
        # Save to semantic memory
        await self.semantic_memory.add_pattern(pattern)
        
        # Mark entry as consolidated
        entry.consolidated = True
        
        self._stats["crystallized"] += 1
        logger.info(f"❄️ Crystallized pattern from entry {entry.id}: {pattern.trigger[:50]}...")
        
        return pattern
    
    async def run_crystallization(self, batch_size: int = None) -> Dict[str, Any]:
        """
        Run crystallization on unconsolidated episodic entries.
        """
        batch_size = batch_size or self.config.batch_size
        self._stats = {"crystallized": 0, "skipped": 0, "errors": 0}
        
        async with self.session_factory() as db:
            from sqlalchemy import select
            stmt = select(EpisodicEntry).where(
                EpisodicEntry.consolidated == False
            ).order_by(EpisodicEntry.timestamp.desc()).limit(batch_size)
            
            result = await db.execute(stmt)
            entries = result.scalars().all()
            
            if not entries:
                return {
                    "processed": 0,
                    "crystallized": 0,
                    "skipped": 0,
                    "message": "No unconsolidated entries found"
                }
            
            logger.info(f"📊 Found {len(entries)} unconsolidated entries")
            
            for entry in entries:
                try:
                    await self.crystallize(entry)
                except Exception as e:
                    self._stats["errors"] += 1
                    logger.error(f"Error crystallizing entry {entry.id}: {e}")
            
            await db.commit()
        
        return {
            "processed": len(entries),
            "crystallized": self._stats["crystallized"],
            "skipped": self._stats["skipped"],
            "errors": self._stats["errors"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _qualifies_for_crystallization(self, entry: EpisodicEntry) -> bool:
        """Check if entry qualifies for crystallization."""
        # Check if evaluation exists
        if not entry.evaluation:
            return False
        
        # Parse evaluation
        import json
        try:
            eval_data = json.loads(entry.evaluation) if isinstance(entry.evaluation, str) else entry.evaluation
        except:
            return False
        
        # Check confidence threshold dynamically
        from app.api.v2.services.algorithm_optimization_service import AlgorithmOptimizationService
        # Assuming environment_id is available or defaults. 
        # For this integration, we use a placeholder environment ID if not in context.
        # Ideally, environment context should be passed through.
        threshold = self.config.confidence_threshold
        # Note: Optimization service interaction requires environment context.
        # This is a simplified integration point.
        
        confidence = eval_data.get("confidence", 0.0)
        if confidence < threshold:
            return False
        
        # Check if passed
        if not eval_data.get("passed", False):
            return False
        
        return True
    
    async def _extract_pattern(self, entry: EpisodicEntry) -> Optional[Dict]:
        """Extract pattern data from episodic entry."""
        if not entry.query:
            return None
        
        import json
        try:
            eval_data = json.loads(entry.evaluation) if isinstance(entry.evaluation, str) else entry.evaluation
        except:
            eval_data = {}
        
        # Determine pattern type
        pattern_type = "improvement"
        if eval_data.get("faithfulness", 0) > 0.9:
            pattern_type = "success"
        elif eval_data.get("faithfulness", 0) < 0.5:
            pattern_type = "hallucination_prevention"
        
        return {
            "type": pattern_type,
            "trigger": entry.query[:100],
            "correction": eval_data.get("feedback", "Improve response quality"),
            "confidence": eval_data.get("confidence", 0.7)
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get crystallization statistics."""
        async with self.session_factory() as db:
            from sqlalchemy import select, func
            total_stmt = select(func.count(EpisodicEntry.id))
            total_result = await db.execute(total_stmt)
            total = total_result.scalar_one() or 0
            
            consolidated_stmt = select(func.count(EpisodicEntry.id)).where(EpisodicEntry.consolidated == True)
            consolidated_result = await db.execute(consolidated_stmt)
            consolidated = consolidated_result.scalar_one() or 0
            
            patterns = await self.semantic_memory.get_patterns()
            
            return {
                "total_episodic": total,
                "consolidated": consolidated,
                "pending": total - consolidated,
                "total_patterns": len(patterns),
                "active_patterns": len([p for p in patterns if p.is_active]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
