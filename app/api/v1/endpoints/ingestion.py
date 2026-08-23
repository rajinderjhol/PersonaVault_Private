"""
Document Ingestion API - Upload and process documents for evidence extraction.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.services.evidence_extractor import EvidenceExtractor
from app.services.decision_linkage import DecisionLinkageEngine
from pydantic import BaseModel
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

class LinkEvidenceRequest(BaseModel):
    evidence_ids: List[int]
    confidence: float = 0.8
    reasoning: str = ""

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    metadata: Optional[str] = None
):
    """
    Upload a document for evidence extraction.
    """
    try:
        content = await file.read()
        file_type = file.filename.split('.')[-1].lower()
        
        meta = json.loads(metadata) if metadata else {}
        
        extractor = EvidenceExtractor(db)
        result = await extractor.extract_from_document(
            content=content,
            filename=file.filename,
            file_type=file_type,
            metadata=meta
        )
        
        return {
            "status": "success",
            "job_id": result["job_id"],
            "total_blocks": result["total_blocks"],
            "qualified_blocks": result["qualified_blocks"],
            "blocks": result["blocks"]
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/link/{decision_id}")
async def link_evidence_to_decision(
    decision_id: int,
    request: LinkEvidenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link evidence blocks to a decision.
    """
    try:
        linker = DecisionLinkageEngine(db)
        result = await linker.link_to_decision(
            decision_id=decision_id,
            evidence_ids=request.evidence_ids,
            confidence=request.confidence,
            reasoning=request.reasoning
        )
        
        return {"status": "success", "result": result}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Link error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evidence/{decision_id}")
async def get_evidence_for_decision(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all evidence linked to a decision.
    """
    linker = DecisionLinkageEngine(db)
    return await linker.get_evidence_for_decision(decision_id)

@router.get("/stats")
async def get_evidence_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get evidence statistics.
    """
    linker = DecisionLinkageEngine(db)
    return await linker.get_evidence_stats()

@router.get("/blocks")
async def list_evidence_blocks(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List evidence blocks.
    """
    from sqlalchemy import select
    from app.models.evidence import EvidenceBlock
    
    stmt = select(EvidenceBlock).order_by(EvidenceBlock.extracted_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    blocks = result.scalars().all()
    
    return {
        "total": len(blocks),
        "blocks": [
            {
                "id": b.id,
                "block_id": b.block_id,
                "content": b.content[:300] + "..." if len(b.content) > 300 else b.content,
                "source": b.source,
                "source_type": b.source_type,
                "confidence": b.confidence,
                "quality_score": b.quality_score,
                "is_qualified": b.is_qualified,
                "tags": b.tags,
                "extracted_at": b.extracted_at.isoformat()
            }
            for b in blocks
        ]
    }
