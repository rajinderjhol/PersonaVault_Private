"""
Document Ingestion Endpoint - Ingest documents from folders
"""

import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.ingestion.document_ingestion import DocumentIngestionService
from app.models.evidence import BulkIngestionJob
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


class FolderIngestionRequest(BaseModel):
    folder_path: str
    user_id: int = 1
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


@router.post("/folder", response_model=dict)
async def ingest_folder_async(
    request: FolderIngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Start bulk ingestion from a folder.
    """
    job_id = str(uuid.uuid4())
    job = BulkIngestionJob(
        job_id=job_id,
        folder_path=request.folder_path,
        status="pending"
    )
    db.add(job)
    await db.commit()
    
    background_tasks.add_task(
        _run_bulk_ingestion, 
        job_id, request.folder_path, request.user_id, request.recursive, request.max_files
    )
    
    return {"job_id": job_id, "status": "pending"}


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get status of an ingestion job.
    """
    stmt = select(BulkIngestionJob).where(BulkIngestionJob.job_id == job_id)
    job = (await db.execute(stmt)).scalars().first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        folder_path=job.folder_path,
        total_files=job.total_files,
        successful_files=job.successful_files,
        failed_files=job.failed_files
    )
