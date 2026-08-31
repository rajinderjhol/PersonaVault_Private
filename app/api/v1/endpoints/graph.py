from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.graph_builder_service import GraphBuilderService

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

@router.get("/decision/{decision_id}")
async def get_decision_graph(decision_id: str, db: AsyncSession = Depends(get_db)):
    service = GraphBuilderService(db)
    return await service.get_decision_provenance_graph(decision_id)
