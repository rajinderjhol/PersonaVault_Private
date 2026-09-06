from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime
import logging

from app.db.session import get_db
from app.api.v2.models.environment import Environment
from app.api.v2.dependencies import require_membership
from app.services.ingestion.document_ingestion import DocumentIngestionService
from app.models.evidence import BulkIngestionJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/{env_id}/ingestion", tags=["v2-ingestion"])

class FolderIngestionRequest(BaseModel):
    folder_path: str
    recursive: bool = True
    max_files: Optional[int] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    folder_path: str
    total_files: int
    successful_files: int
    failed_files: int

async def _run_bulk_ingestion(job_id: str, folder_path: str, user_id: int, recursive: bool, max_files: Optional[int]):
    """Background task to process bulk ingestion."""
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        stmt = select(BulkIngestionJob).where(BulkIngestionJob.job_id == job_id)
        job = (await db.execute(stmt)).scalars().first()
        if not job:
            return
        
        job.status = "processing"
        await db.commit()
        
        try:
            service = DocumentIngestionService()
            results = await service.ingest_folder(
                folder_path=folder_path,
                user_id=user_id,
                recursive=recursive,
                max_files=max_files
            )
            
            successful = [r for r in results if r.status == "success"]
            failed = [r for r in results if r.status == "failed"]
            
            job.status = "completed"
            job.total_files = len(results)
            job.successful_files = len(successful)
            job.failed_files = len(failed)
            job.completed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            logger.error(f"Bulk ingestion error: {e}")
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()

@router.post("/folder", response_model=Dict[str, str])
async def ingest_folder_async(
    env_id: str,
    request: FolderIngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    env: Environment = Depends(require_membership)
):
    """Start bulk ingestion from a folder (V2)."""
    job_id = str(uuid.uuid4())
    job = BulkIngestionJob(
        job_id=job_id,
        folder_path=request.folder_path,
        status="pending"
    )
    db.add(job)
    await db.commit()
    
    # We use env.owner_id as a proxy for user_id for now
    background_tasks.add_task(
        _run_bulk_ingestion, 
        job_id, request.folder_path, int(env.owner_principal_id), request.recursive, request.max_files
    )
    
    return {"job_id": job_id, "status": "pending"}

@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(env_id: str, job_id: str, db: AsyncSession = Depends(get_db), env: Environment = Depends(require_membership)):
    """Get status of an ingestion job."""
    stmt = select(BulkIngestionJob).where(BulkIngestionJob.job_id == job_id)
    job = (await db.execute(stmt)).scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        folder_path=job.folder_path,
        total_files=job.total_files or 0,
        successful_files=job.successful_files or 0,
        failed_files=job.failed_files or 0
    )
