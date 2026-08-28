from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
import io

from app.models.marketplace import (
    PackUploadRequest, PackReviewRequest,
    MarketplacePack, PackCategory
)
from app.services.marketplace.pack_manager import PackManager
from app.services.marketplace.registry import MarketplaceRegistry

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])

# Initialize services
pack_manager = PackManager()
registry = MarketplaceRegistry()


@router.get("/packs")
async def list_packs(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name/description"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List available packs in the marketplace."""
    result = registry.list_packs(
        category=category,
        search=search,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset
    )
    
    # Add installation status
    installed = set(p["id"] for p in pack_manager.get_installed_packs())
    for pack in result["packs"]:
        pack["is_installed"] = pack.get("id") in installed
    
    return result


@router.get("/packs/{pack_id}")
async def get_pack(pack_id: str):
    """Get detailed information about a pack."""
    pack = registry.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Add installation status
    installed = [p["id"] for p in pack_manager.get_installed_packs()]
    pack["is_installed"] = pack_id in installed
    
    return pack


@router.post("/packs/upload")
async def upload_pack(
    file: UploadFile = File(...),
    name: str = Query(...),
    domain: str = Query(...),
    description: str = Query(...),
    category: PackCategory = Query(...),
    version: str = Query("1.0.0"),
    tags: str = Query("")
):
    """Upload a pack to the marketplace."""
    try:
        # Read file
        content = await file.read()
        
        # Register pack
        metadata = {
            "name": name,
            "domain": domain,
            "description": description,
            "category": category.value,
            "version": version,
            "tags": tags.split(",") if tags else [],
            "status": "published"
        }
        
        # Use name as pack_id for simplicity
        pack_id = name.lower().replace(" ", "_")
        
        registry.register_pack(pack_id, metadata)
        
        # Install pack locally (optional)
        result = await pack_manager.install_pack(content, pack_id, version)
        
        return {
            "success": True,
            "pack_id": pack_id,
            "version": version,
            "install_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/packs/{pack_id}/install")
async def install_pack(pack_id: str):
    """Install a pack from the marketplace."""
    pack = registry.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    # Check if already installed
    installed = [p["id"] for p in pack_manager.get_installed_packs()]
    if pack_id in installed:
        return {"success": True, "message": "Pack already installed"}
    
    # In a real implementation, download from a CDN/URL
    # For now, return instructions
    return {
        "success": False,
        "message": "Pack download URL not configured",
        "pack_id": pack_id,
        "pack_data": pack
    }


@router.post("/packs/{pack_id}/uninstall")
async def uninstall_pack(pack_id: str):
    """Uninstall a pack."""
    result = await pack_manager.uninstall_pack(pack_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/packs/{pack_id}/review")
async def review_pack(
    pack_id: str,
    review: PackReviewRequest
):
    """Add a review for a pack."""
    result = registry.add_review(
        pack_id=pack_id,
        rating=review.rating,
        comment=review.comment
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Pack not found")
    
    return {"success": True, "review": result}


@router.get("/categories")
async def list_categories():
    """List all available pack categories."""
    return {
        "categories": [c.value for c in PackCategory]
    }


@router.get("/installed")
async def get_installed_packs():
    """Get all installed packs."""
    return {
        "packs": pack_manager.get_installed_packs()
    }
