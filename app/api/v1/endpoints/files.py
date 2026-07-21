import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.api.v1.endpoints.auth import get_current_user_id

router = APIRouter()

UPLOAD_DIR = "storage/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB Limit
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    user_id: int = Depends(get_current_user_id)
):
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    safe_name = f"{file_id}{extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    
    try:
        with open(file_path, "wb") as buffer:
            size = 0
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large")
                buffer.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    return {
        "id": file_id,
        "filename": file.filename,
        "path": safe_name
    }

@router.get("/{filename}")
async def get_file(filename: str, user_id: int = Depends(get_current_user_id)):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)