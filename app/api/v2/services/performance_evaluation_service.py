from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.repositories.sqlalchemy.semantic_pattern import SQLSemanticPatternRepository
from app.services.memory_service import MemoryService
from app.services.crystallization_service import CrystallizationService

class PerformanceEvaluationService:
    """
    Evaluates the performance of the learning system, including pattern accuracy,
    learning speed, and retrieval quality.
    """
    
    def __init__(
        self,
        pattern_repository: SQLSemanticPatternRepository,
        memory_service: MemoryService,
        crystallization_service: CrystallizationService
    ):
        self.pattern_repository = pattern_repository
        self.memory_service = memory_service
        self.crystallization_service = crystallization_service
        
    async def get_performance_metrics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculates aggregate performance metrics for the learning system.
        """
        # Collect metrics from various components
        accuracy = await self._calculate_pattern_accuracy()
        speed = await self._calculate_learning_speed(days)
        retrieval = await self._calculate_retrieval_quality()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "pattern_accuracy": accuracy,
                "learning_speed": speed,
                "retrieval_quality": retrieval
            }
        }
    
    async def _calculate_pattern_accuracy(self) -> float:
        """
        Calculates the average confidence/success rate of crystallized patterns.
        """
        patterns = await self.pattern_repository.get_all()
        if not patterns:
            return 0.0
            
        # Example metric: Average weight/confidence of crystallized patterns
        total_weight = sum(p.weight for p in patterns if hasattr(p, 'weight'))
        return total_weight / len(patterns)
    
    async def _calculate_learning_speed(self, days: int) -> float:
        """
        Calculates the rate of crystallization (patterns per day).
        """
        patterns = await self.pattern_repository.get_all()
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent_patterns = [p for p in patterns if hasattr(p, 'created_at') and p.created_at >= cutoff]
        return len(recent_patterns) / days
    
    async def _calculate_retrieval_quality(self) -> float:
        """
        Evaluates the effectiveness of pattern retrieval.
        """
        # Placeholder: This would integrate with a feedback loop 
        # (e.g., user feedback on retrieved patterns)
        return 0.85
