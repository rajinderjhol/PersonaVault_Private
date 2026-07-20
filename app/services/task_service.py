import logging
from sqlalchemy import delete
from app.db.session import SessionLocal
from app.models import SemanticPattern
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Create global scheduler instance
scheduler = AsyncIOScheduler()

def init_scheduler():
    """Initialize background scheduler for maintenance tasks."""
    if not scheduler.running:
        scheduler.add_job(sublimation_task, IntervalTrigger(hours=24))
        scheduler.start()
        logger.info("Maintenance scheduler initialized.")
    return scheduler

async def sublimation_task():
    """Prune brittle semantic patterns."""
    try:
        async with SessionLocal() as db:
            stmt = delete(SemanticPattern).where(
                SemanticPattern.confidence < 0.2
            )
            result = await db.execute(stmt)
            await db.commit()
            logger.info(f"Sublimation complete: {result.rowcount} patterns pruned")
    except Exception as e:
        logger.error(f"Sublimation task failed: {e}")

# Export the functions explicitly
__all__ = ['init_scheduler', 'scheduler', 'sublimation_task']