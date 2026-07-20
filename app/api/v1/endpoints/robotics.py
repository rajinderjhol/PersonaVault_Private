from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.perception import RoboticsPerceptionService
from app.services.experience import ExperienceLearningService
from app.services.hri import HRIMemoryService
from app.core.dependencies import require_memory_write

router = APIRouter(prefix="/robotics", tags=["robotics"])

@router.post("/observe")
async def robot_observation(
    observation: dict,
    robot_id: str,
    user_id: int = Depends(require_memory_write),
    db: AsyncSession = Depends(get_db)
):
    service = RoboticsPerceptionService(db)
    return await service.process_robot_observation(observation, robot_id, user_id)

@router.post("/learn")
async def robot_learn(
    request: Request,
    task_id: str,
    description: str,
    result: dict,
    robot_id: str,
    user_id: int = Depends(require_memory_write),
    db: AsyncSession = Depends(get_db)
):
    service = ExperienceLearningService(db, request.app.state.orchestrator)
    return await service.learn_from_task(task_id, description, result, robot_id, user_id)

@router.post("/hri")
async def robot_interaction(
    robot_id: str,
    interaction_text: str,
    user_id: int = Depends(require_memory_write),
    db: AsyncSession = Depends(get_db)
):
    service = HRIMemoryService(db)
    interaction_id = await service.store_interaction(user_id, robot_id, interaction_text)
    return {"status": "success", "memory_id": interaction_id}