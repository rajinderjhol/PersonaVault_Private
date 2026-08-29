"""
Document Ingestion Endpoint - Ingest documents from folders
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.ingestion.document_ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


class FolderIngestionRequest(BaseModel):
    folder_path: str
    user_id: int = 1
    recursive: bool = True
    max_files: Optional[int] = None


class FolderIngestionResponse(BaseModel):
    success: bool
    message: str
    results: list = []
    total_files: int = 0
    successful: int = 0
    failed: int = 0


@router.post("/folder")
async def ingest_folder(
    request: FolderIngestionRequest,
    background_tasks: BackgroundTasks
) -> FolderIngestionResponse:
    """
    Ingest all documents from a folder.
    """
    service = DocumentIngestionService()
    
    try:
        # Run ingestion
        results = await service.ingest_folder(
            folder_path=request.folder_path,
            user_id=request.user_id,
            recursive=request.recursive,
            max_files=request.max_files
        )
        
        successful = [r for r in results if r.status == "success"]
        failed = [r for r in results if r.status == "failed"]
        
        return FolderIngestionResponse(
            success=True,
            message=f"Processed {len(results)} files",
            results=[{
                "doc_name": r.doc_name,
                "status": r.status,
                "patterns": r.patterns_crystallized if r.status == "success" else 0,
                "error": r.error if r.status == "failed" else None
            } for r in results],
            total_files=len(results),
            successful=len(successful),
            failed=len(failed)
        )
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}")
async def get_ingestion_status(user_id: int):
    """
    Get ingestion status for a user.
    """
    service = DocumentIngestionService()
    return await service.get_ingestion_status(user_id)


@router.get("/supported-extensions")
async def get_supported_extensions():
    """
    Get list of supported file extensions.
    """
    return {
        "extensions": list(DocumentIngestionService.SUPPORTED_EXTENSIONS)
    }
