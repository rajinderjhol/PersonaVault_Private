"""
Phase 10.2: Reinforcement Engine
Weights patterns based on success/failure outcomes.
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from app.models import SemanticPattern
from app.services.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)

@dataclass
class ReinforcementConfig:
    """Configuration for reinforcement learning."""
    success_increment: float = 0.05  # Weight increase on success
    failure_decrement: float = 0.10   # Weight decrease on failure
    decay_rate: float = 0.01         # Weekly decay for unused patterns
    min_weight: float = 0.10         # Minimum weight before deactivation
    max_weight: float = 1.0          # Maximum weight cap
    activation_threshold: float = 0.40  # Weight threshold for activation
    decay_period_hours: float = 168  # 7 days


class ReinforcementEngine:
    """
    Reinforces patterns based on outcomes and decays unused patterns.
    """
    
    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
        self.config = ReinforcementConfig()
        self._pattern_history: Dict[int, List[Dict]] = {}
    
    async def reinforce_pattern(self, pattern_id: int, outcome: str, confidence: float = 0.5) -> Dict[str, Any]:
        """
        Reinforce a pattern based on outcome.
        
        Args:
            pattern_id: ID of the pattern to reinforce
            outcome: 'success', 'failure', or 'neutral'
            confidence: Confidence level of the outcome (0.0 - 1.0)
        
        Returns:
            Dict with updated pattern info
        """
        # Get the pattern
        patterns = await self.semantic_memory.get_patterns()
        pattern = next((p for p in patterns if p.id == pattern_id), None)
        
        if not pattern:
            logger.warning(f"Pattern {pattern_id} not found")
            return {"error": "Pattern not found"}
        
        # Record history
        if pattern_id not in self._pattern_history:
            self._pattern_history[pattern_id] = []
        self._pattern_history[pattern_id].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcome": outcome,
            "confidence": confidence,
            "old_weight": pattern.weight
        })
        
        # Update weight based on outcome
        old_weight = pattern.weight
        
        if outcome == "success":
            increment = self.config.success_increment * confidence
            pattern.weight = min(self.config.max_weight, pattern.weight + increment)
            pattern.success_count += 1
            logger.info(f"✅ Pattern {pattern_id} reinforced: +{increment:.3f} (weight: {pattern.weight:.3f})")
            
        elif outcome == "failure":
            decrement = self.config.failure_decrement * (1 + (1 - confidence))
            pattern.weight = max(self.config.min_weight, pattern.weight - decrement)
            logger.info(f"❌ Pattern {pattern_id} weakened: -{decrement:.3f} (weight: {pattern.weight:.3f})")
            
        else:  # neutral
            pattern.weight = max(self.config.min_weight, pattern.weight - 0.01)
            logger.info(f"➖ Pattern {pattern_id} slightly decayed: weight {pattern.weight:.3f}")
        
        # Check activation status
        if pattern.weight < self.config.activation_threshold and pattern.is_active:
            pattern.is_active = False
            logger.info(f"🔴 Pattern {pattern_id} deactivated (weight: {pattern.weight:.3f})")
        elif pattern.weight >= self.config.activation_threshold and not pattern.is_active:
            pattern.is_active = True
            logger.info(f"🟢 Pattern {pattern_id} activated (weight: {pattern.weight:.3f})")
        
        # Update timestamp
        pattern.updated_at = datetime.now(timezone.utc)
        
        # Save changes
        await self._save_pattern(pattern)
        
        return {
            "pattern_id": pattern_id,
            "old_weight": old_weight,
            "new_weight": pattern.weight,
            "is_active": pattern.is_active,
            "success_count": pattern.success_count,
            "outcome": outcome,
            "confidence": confidence
        }
    
    async def decay_unused_patterns(self) -> Dict[str, Any]:
        """
        Decay patterns that haven't been used recently.
        """
        patterns = await self.semantic_memory.get_patterns()
        decayed = 0
        deactivated = 0
        
        now = datetime.now(timezone.utc)
        decay_period = timedelta(hours=self.config.decay_period_hours)
        
        for pattern in patterns:
            if not pattern.is_active:
                continue
            
            # Check if pattern has been used recently
            last_used = pattern.updated_at or pattern.created_at
            time_since_use = now - last_used
            
            if time_since_use > decay_period:
                # Apply decay based on how long it's been unused
                weeks_unused = time_since_use.total_seconds() / (7 * 24 * 3600)
                decay_amount = min(0.05, weeks_unused * self.config.decay_rate)
                pattern.weight = max(self.config.min_weight, pattern.weight - decay_amount)
                pattern.updated_at = now
                
                logger.info(f"📉 Pattern {pattern.id} decayed: -{decay_amount:.3f} (weight: {pattern.weight:.3f})")
                decayed += 1
                
                # Check if it should be deactivated
                if pattern.weight < self.config.activation_threshold:
                    pattern.is_active = False
                    deactivated += 1
                    logger.info(f"🔴 Pattern {pattern.id} deactivated due to decay")
        
        return {
            "patterns_checked": len(patterns),
            "patterns_decayed": decayed,
            "patterns_deactivated": deactivated,
            "timestamp": now.isoformat()
        }
    
    async def batch_reinforce(self, feedback_items: List[Dict]) -> Dict[str, Any]:
        """
        Batch reinforce multiple patterns at once.
        """
        results = []
        errors = []
        
        for item in feedback_items:
            pattern_id = item.get("pattern_id")
            outcome = item.get("outcome", "neutral")
            confidence = item.get("confidence", 0.5)
            
            if not pattern_id:
                errors.append({"error": "Missing pattern_id", "item": item})
                continue
            
            try:
                result = await self.reinforce_pattern(pattern_id, outcome, confidence)
                results.append(result)
            except Exception as e:
                errors.append({"error": str(e), "item": item})
        
        return {
            "total": len(feedback_items),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    async def get_reinforcement_stats(self) -> Dict[str, Any]:
        """
        Get reinforcement statistics.
        """
        patterns = await self.semantic_memory.get_patterns()
        active = [p for p in patterns if p.is_active]
        
        # Calculate weight distribution
        weight_dist = {
            "high": len([p for p in active if p.weight >= 0.8]),
            "medium": len([p for p in active if 0.5 <= p.weight < 0.8]),
            "low": len([p for p in active if p.weight < 0.5])
        }
        
        return {
            "total_patterns": len(patterns),
            "active_patterns": len(active),
            "weight_distribution": weight_dist,
            "avg_weight": sum(p.weight for p in active) / len(active) if active else 0,
            "history_count": sum(len(h) for h in self._pattern_history.values()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _save_pattern(self, pattern: SemanticPattern):
        """Save pattern changes."""
        # Ensure changes are persisted via the semantic memory/repository
        await self.semantic_memory.repository.update(pattern)
