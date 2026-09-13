from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.v2.models.intelligence_pack import V2IntelligencePack
from app.api.v2.adapters.pack_adapter import PackAdapter
from app.services.packs.pack_loader import PackLoader
from app.db.session import SessionLocal

router = APIRouter(tags=["v2-intelligence-packs"])

# In a real app, this would be injected via FastAPI dependency
def get_pack_loader():
    # PackLoader expects a session_factory, which SessionLocal is.
    return PackLoader(session_factory=SessionLocal)

@router.get("/{env_id}/packs/", response_model=List[V2IntelligencePack])
async def get_intelligence_packs(env_id: str, loader: PackLoader = Depends(get_pack_loader)):
    """Get V2 Intelligence Packs adapted from V1 Behavior Packs."""
    # List installed V1 packs using the service
    v1_packs = await loader.list_installed_packs()
    
    # Adapt them to V2 Intelligence Packs
    v2_packs = []
    for pack in v1_packs:
        v1_pack_dict = {
            "id": pack.id,
            "name": pack.name,
            "domain": pack.domain,
            "version": pack.version,
            "description": pack.description,
            "rules": pack.policies 
        }
        v2_packs.append(PackAdapter.from_v1_behavior_pack(v1_pack_dict))
        
    return v2_packs
