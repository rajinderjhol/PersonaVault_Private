from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.lineage.lineage_service import LineageService
from app.models.lineage import DeletionRequest

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


class DeletionRequestCreate(BaseModel):
    user_id: int
    target_ids: List[str]
    request_type: str = "delete_user_data"
    explanation: Optional[str] = None


class DeletionRequestResponse(BaseModel):
    id: str
    user_id: int
    status: str
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


@router.get("/lineage/node/{node_id}")
async def get_lineage(
    node_id: str,
    depth: int = Query(3, ge=1, le=5)
):
    """Get the full lineage graph for a node."""
    service = LineageService()
    try:
        return await service.get_lineage(node_id, depth)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/lineage/user/{user_id}")
async def get_user_data(user_id: int):
    """Get all data lineage for a user."""
    service = LineageService()
    return await service.get_user_data(user_id)


@router.post("/deletion/request")
async def create_deletion_request(
    request: DeletionRequestCreate
):
    """Create a deletion request."""
    service = LineageService()
    try:
        result = await service.create_deletion_request(
            user_id=request.user_id,
            target_ids=request.target_ids,
            request_type=request.request_type,
            explanation=request.explanation
        )
        return {
            "request_id": result.id,
            "status": result.status,
            "created_at": result.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deletion/request/{request_id}/process")
async def process_deletion_request(request_id: str):
    """Process a deletion request."""
    service = LineageService()
    try:
        result = await service.process_deletion_request(request_id)
        return {
            "request_id": result.request_id,
            "success": result.success,
            "deleted_nodes": result.deleted_nodes,
            "invalidated_patterns": result.invalidated_patterns,
            "errors": result.errors
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deletion/request/{request_id}/status")
async def get_deletion_request_status(request_id: str):
    """Get the status of a deletion request."""
    service = LineageService()
    try:
        return await service.get_deletion_request_status(request_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/deletion/requests/user/{user_id}")
async def get_user_deletion_requests(user_id: int):
    """Get all deletion requests for a user."""
    service = LineageService()
    requests = [r for r in service.requests if r.user_id == user_id]
    return {
        "user_id": user_id,
        "requests": [
            {
                "id": r.id,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "target_count": len(r.target_ids)
            }
            for r in requests
        ]
    }


@router.get("/statistics")
async def get_privacy_statistics():
    """Get privacy and lineage statistics."""
    service = LineageService()
    return await service.get_statistics()


@router.get("/gdpr/compliance")
async def get_gdpr_compliance_status():
    """Get GDPR compliance status."""
    service = LineageService()
    stats = await service.get_statistics()
    
    return {
        "gdpr_ready": True,
        "features": {
            "data_lineage": True,
            "right_to_forget": True,
            "deletion_workflow": True,
            "audit_trail": True,
            "data_inventory": True
        },
        "statistics": stats
    }
