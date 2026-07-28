"""
Behaviour Pack API endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.packs.pack_loader import PackLoader
import yaml

router = APIRouter(prefix="/packs", tags=["behaviour-packs"])

@router.get("/")
async def list_packs(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all installed behaviour packs."""
    loader = PackLoader(lambda: db)
    packs = await loader.list_packs()
    return {
        "total": len(packs),
        "packs": [{
            "id": p.id,
            "name": p.name,
            "version": p.version,
            "domain": p.domain,
            "description": p.description,
            "is_active": p.is_active
        } for p in packs]
    }

@router.post("/install")
async def install_pack(
    file: UploadFile = File(...),
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Install a behaviour pack from YAML."""
    try:
        content = await file.read()
        yaml_content = content.decode('utf-8')
        
        loader = PackLoader(lambda: db)
        pack = await loader.load_pack_from_yaml(yaml_content, user_id)
        
        if not pack:
            raise HTTPException(status_code=400, detail="Invalid pack file")
        
        success = await loader.install_pack(pack)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to install pack")
        
        return {
            "status": "success",
            "pack_id": pack.id,
            "name": pack.name,
            "domain": pack.domain
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@router.get("/{pack_id}")
async def get_pack(
    pack_id: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific pack."""
    loader = PackLoader(lambda: db)
    pack = await loader.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    return {
        "id": pack.id,
        "name": pack.name,
        "version": pack.version,
        "domain": pack.domain,
        "description": pack.description,
        "entities": pack.entities,
        "events": pack.events,
        "decision_types": pack.decision_types,
        "metrics": pack.metrics,
        "policies": pack.policies,
        "evaluation_rules": pack.evaluation_rules
    }
