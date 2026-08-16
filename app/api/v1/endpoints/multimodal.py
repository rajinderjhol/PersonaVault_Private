"""
Multimodal Intelligence API endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.services.multimodal import MultimodalIntelligence
import base64

router = APIRouter(prefix="/api/v1/multimodal", tags=["multimodal"])

@router.post("/document")
async def process_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process a document file."""
    content = await file.read()
    file_type = file.filename.split('.')[-1]
    service = MultimodalIntelligence(db)
    return await service.process_document(content, file_type)

@router.post("/image")
async def process_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process an image file."""
    content = await file.read()
    file_type = file.filename.split('.')[-1]
    service = MultimodalIntelligence(db)
    return await service.process_image(content, file_type)

@router.post("/audio")
async def process_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process an audio file."""
    content = await file.read()
    file_type = file.filename.split('.')[-1]
    service = MultimodalIntelligence(db)
    return await service.process_audio(content, file_type)
