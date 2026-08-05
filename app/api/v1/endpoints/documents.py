"""
Document upload and processing endpoints for PersonaVault.
Supports PDF, Word, Excel, and text files.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
from datetime import datetime
import uuid
import asyncio
from typing import Optional, List, Dict, Any

from app.core.dependencies import get_current_user
from app.db.session import get_db, SessionLocal
from app.services.vector_service import vector_service
from app.models import Memory, User

router = APIRouter(prefix="/documents", tags=["documents"])

# Ensure upload directory exists
UPLOAD_DIR = "storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def get_user_id(current_user) -> int:
    """Extract user ID from current user object."""
    if hasattr(current_user, 'id'):
        return current_user.id
    elif isinstance(current_user, int):
        return current_user
    return 1  # fallback


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document."""
    try:
        user_id = await get_user_id(current_user)
        
        # Validate file type
        allowed_extensions = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md", ".csv"]
        filename = file.filename or "untitled"
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        
        if ext not in allowed_extensions:
            raise HTTPException(400, f"File type {ext} not supported. Allowed: {', '.join(allowed_extensions)}")
        
        # Save file
        safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Extract text based on file type
        text_content = await extract_text(file_path, filename)
        
        if not text_content or len(text_content.strip()) < 10:
            os.remove(file_path)
            raise HTTPException(400, "Could not extract text from document. File may be empty or corrupted.")
        
        # Create memory entry
        memory = Memory(
            user_id=user_id,
            title=f"Document: {filename}",
            content=text_content[:10000],
            tags=f"document,{ext[1:] if ext else 'unknown'}",
            modality="document",
            extra_data={
                "filename": filename,
                "file_path": file_path,
                "file_size": len(content),
                "file_type": ext[1:] if ext else "unknown",
                "uploaded_at": datetime.now().isoformat()
            }
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        # Index in vector store (async)
        asyncio.create_task(index_document(memory.id, text_content, user_id))
        
        return {
            "status": "success",
            "memory_id": memory.id,
            "filename": filename,
            "content_length": len(text_content),
            "file_size": len(content),
            "message": "Document uploaded and indexed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Upload failed: {str(e)}")


async def index_document(memory_id: int, content: str, user_id: int):
    """Index document in vector store asynchronously."""
    try:
        await vector_service.index_memory(memory_id, content, user_id)
        print(f"✅ Indexed document {memory_id}")
    except Exception as e:
        print(f"❌ Failed to index document {memory_id}: {e}")


async def extract_text(file_path: str, filename: str) -> str:
    """Extract text from various document types."""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    try:
        if ext == ".pdf":
            return await extract_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return await extract_word(file_path)
        elif ext in [".xlsx", ".xls"]:
            return await extract_excel(file_path)
        elif ext in [".txt", ".md", ".csv"]:
            return await extract_text_file(file_path)
        else:
            return ""
    except Exception as e:
        print(f"Extraction error for {filename}: {e}")
        return ""


async def extract_pdf(file_path: str) -> str:
    """Extract text from PDF."""
    try:
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join([page.extract_text() or "" for page in reader.pages])
            return text
    except ImportError:
        return "[PyPDF2 not installed. Please install: pip install PyPDF2]"
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"


async def extract_word(file_path: str) -> str:
    """Extract text from Word document."""
    try:
        import docx
        doc = docx.Document(file_path)
        return " ".join([para.text for para in doc.paragraphs])
    except ImportError:
        return "[python-docx not installed. Please install: pip install python-docx]"
    except Exception as e:
        return f"[Word extraction error: {str(e)}]"


async def extract_excel(file_path: str) -> str:
    """Extract text from Excel spreadsheet."""
    try:
        import pandas as pd
        df = pd.read_excel(file_path, sheet_name=None)
        text_parts = []
        for sheet_name, sheet_df in df.items():
            text_parts.append(f"Sheet: {sheet_name}")
            text_parts.append(sheet_df.to_string())
        return "\n".join(text_parts)
    except ImportError:
        return "[pandas not installed. Please install: pip install pandas openpyxl]"
    except Exception as e:
        return f"[Excel extraction error: {str(e)}]"


async def extract_text_file(file_path: str) -> str:
    """Extract text from text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[Text extraction error: {str(e)}]"


@router.get("/list")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all uploaded documents."""
    from sqlalchemy import select
    user_id = await get_user_id(current_user)
    
    stmt = select(Memory).where(
        Memory.user_id == user_id,
        Memory.modality == "document"
    ).order_by(Memory.created_at.desc())
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return {
        "documents": [{
            "id": d.id,
            "title": d.title,
            "content_preview": d.content[:200] + "..." if len(d.content) > 200 else d.content,
            "file_type": d.extra_data.get("file_type", "unknown"),
            "file_size": d.extra_data.get("file_size", 0),
            "created_at": d.created_at.isoformat(),
            "tags": d.tags
        } for d in documents]
    }


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    from sqlalchemy import select, delete
    user_id = await get_user_id(current_user)
    
    stmt = select(Memory).where(Memory.id == doc_id, Memory.user_id == user_id)
    result = await db.execute(stmt)
    memory = result.scalars().first()
    
    if not memory:
        raise HTTPException(404, "Document not found")
    
    # Delete file if exists
    file_path = memory.extra_data.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    await db.execute(delete(Memory).where(Memory.id == doc_id))
    await db.commit()
    
    return {"status": "success", "message": "Document deleted"}
