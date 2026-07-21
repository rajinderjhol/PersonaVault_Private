import asyncio
import logging
from datetime import datetime
from app.services.task_service import episodic_reflection_task, sublimation_task

logger = logging.getLogger(__name__)

class ConsolidationTask:
    """
    Background task manager for Layer 2 -> Layer 3 memory consolidation.
    Orchestrates the 'Crystallization' and 'Sublimation' cycles.
    """
    def __init__(self, orchestrator, memory_service, config: dict):
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.config = config
        self.batch_size = config.get("batch_size", 10)
        self.interval_hours = config.get("interval_hours", 1)
        self._running = True
        self.trigger_event = asyncio.Event()

    async def run(self):
        """Continuous background loop for cognitive learning."""
        logger.info(f"ConsolidationTask: Engine ignited. Interval: {self.interval_hours}h, Batch: {self.batch_size}")
        
        # Initial cooldown to allow other services to settle
        await asyncio.sleep(30)

        while self._running:
            try:
                logger.info("ConsolidationTask: Starting background reflection cycle...")
                # This task handles the Layer 2 -> Layer 3 pattern graduation
                await episodic_reflection_task()
                
                logger.info("ConsolidationTask: Running sublimation check to prune brittle patterns...")
                await sublimation_task()
                
                logger.info(f"ConsolidationTask: Cycle complete. Next run in {self.interval_hours} hour(s).")
                
                # Wait for the next interval OR for a manual trigger from the dashboard
                try:
                    await asyncio.wait_for(self.trigger_event.wait(), timeout=self.interval_hours * 3600)
                    self.trigger_event.clear()
                    logger.info("ConsolidationTask: Manual trigger received via Admin Dashboard.")
                except asyncio.TimeoutError:
                    pass # Interval elapsed naturally
            except Exception as e:
                logger.error(f"ConsolidationTask loop error: {e}")
                await asyncio.sleep(300) # Wait 5 minutes before retrying on failure