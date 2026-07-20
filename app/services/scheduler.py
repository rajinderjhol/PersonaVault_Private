from apscheduler.schedulers.background import BackgroundScheduler
from app.extensions import db
from app.services.memory_service import MemoryService

scheduler = BackgroundScheduler()

def init_scheduler(app=None):
    """
    Start the scheduler and add jobs.
    """
    # Create the service instance with the current session
    service = MemoryService(db_session=db.session)
    # Schedule the task. service.delete_expired_memories will use its internal self.db
    scheduler.add_job(service.delete_expired_memories, 'interval', days=1)

    # Start the scheduler
    scheduler.start()