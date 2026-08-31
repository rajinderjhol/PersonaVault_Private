"""
Pattern Compiler API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.services.packs.pack_loader import PackLoader

router = APIRouter(prefix="/compiler", tags=["compiler"])

@router.get("/packs")
async def list_compiler_packs(
    user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List packs for the compiler."""
    loader = PackLoader(lambda: db)
    packs = await loader.list_installed_packs()
    return [{
        "id": p.id,
        "name": p.name,
        "version": p.version,
        "domain": p.domain,
        "description": p.description,
        "is_active": p.is_active
    } for p in packs]
