from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models import LegalMatter, LegalDocument
from app.core.dependencies import require_memory_write, require_admin
from app.services.contract_analyzer import ContractAnalyzer
from app.services.research import LegalResearchService
from app.services.drafting import LegalDrafter
from pydantic import BaseModel

router = APIRouter(prefix="/legal", tags=["legal"])

# Add Pydantic model for draft request
class DraftRequest(BaseModel):
    template_text: str
    variables: dict
    instructions: str

@router.post("/matters")
async def create_matter(
    title: str,
    description: str,
    client_id: int,
    assigned_attorney_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new legal matter."""
    matter = LegalMatter(
        matter_number=f"M-{int(time.time())}",
        title=title,
        description=description,
        client_id=client_id,
        assigned_attorney_id=assigned_attorney_id
    )
    db.add(matter)
    await db.commit()
    await db.refresh(matter)
    return matter

@router.post("/documents/analyze")
async def analyze_contract(
    document_id: int,
    user_id: int = Depends(require_memory_write),
    db: AsyncSession = Depends(get_db)
):
    """Analyze a contract using the legal AI pipeline."""
    stmt = select(LegalDocument).where(LegalDocument.id == document_id)
    result = await db.execute(stmt)
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    analyzer = ContractAnalyzer()
    analysis = await analyzer.analyze_contract(document_id, document.content)
    return analysis

@router.post("/research")
async def conduct_legal_research(
    query: str,
    jurisdiction: str = "US",
    user_id: int = Depends(require_memory_write)
):
    """Conduct legal research on a topic."""
    research = LegalResearchService()
    return await research.research_topic(query, jurisdiction)

@router.post("/draft")
async def draft_legal_document(request: DraftRequest):
    """Draft a legal document."""
    drafter = LegalDrafter()
    return await drafter.draft_document(
        request.template_text,
        request.variables,
        request.instructions
    )
