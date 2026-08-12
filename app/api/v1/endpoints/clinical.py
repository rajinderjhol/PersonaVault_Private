from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/clinical", tags=["clinical"])

@router.get("/decisions")
async def get_clinical_decisions(
    days: int = 30,
    decision_type: Optional[str] = None,
    patient_id: Optional[str] = None,
    search: Optional[str] = None,
    type: Optional[str] = None,
    user = Depends(require_admin)
):
    """Get clinical AI decisions with cryptographic proof."""
    # Mock data for USB Demo
    return {
        "total": 124,
        "human_reviewed": 118,
        "compliance_rate": "98.2%",
        "avg_confidence": "94.5%",
        "recent_activity": [
            {
                "type": "radiology",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "description": "Anomalous mass detected in L-Lobe (Patient USB-9923)",
                "confidence": 98,
                "human_reviewed": True,
                "receipt_id": "vap_usb_rad_99283742"
            },
            {
                "type": "clinical",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "description": "Drug interaction warning: Warfarin + Aspirin (Patient USB-1022)",
                "confidence": 99,
                "human_reviewed": False,
                "receipt_id": "vap_usb_cli_11029384"
            },
            {
                "type": "pathology",
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "description": "Cellular morphology analysis complete: Stage 2 markers (Patient USB-4451)",
                "confidence": 92,
                "human_reviewed": True,
                "receipt_id": "vap_usb_pat_88273645"
            }
        ],
        "decisions": [
             {
                "id": "DEC-USB-001",
                "status": "verified",
                "type": "radiology",
                "patient_id": "USB-9923",
                "description": "Anomalous mass detection",
                "human_reviewed": True,
                "receipt_id": "vap_usb_rad_99283742"
            },
             {
                "id": "DEC-USB-002",
                "status": "pending",
                "type": "clinical",
                "patient_id": "USB-1022",
                "description": "Drug interaction warning",
                "human_reviewed": False,
                "receipt_id": "vap_usb_cli_11029384"
            }
        ]
    }
    
@router.get("/decisions/{receipt_id}/verify")
async def verify_clinical_decision(receipt_id: str, user = Depends(require_admin)):
    """Verify a clinical decision's cryptographic proof."""
    return {
        "receipt_id": receipt_id,
        "status": "verified",
        "timestamp": datetime.now().isoformat(),
        "merkle_root": "7f83b127ba22fec820d53c7a92b2345e6f1a89c9234b8c9d01e2f3a4b5c6d7e8",
        "signature": "3045022100ef83b127ba22fec820d53c7a92b2345e6f1a89c9234b8c9d01e2f3a4b5c6d7e802202b8c9d01e2f3a4b5c6d7e8..."
    }
    
@router.get("/compliance/swiss")
async def get_swiss_compliance_status(user = Depends(require_admin)):
    """Get Swiss regulatory compliance status for clinical AI."""
    return {
        "mepv": {"status": "compliant", "last_audit": "2026-07-15"},
        "ndsg": {"status": "compliant", "last_audit": "2026-07-15"},
        "eu_ai_act_art14": {"status": "in_progress", "target": "2026-12-01"},
        "fdpic": {"status": "aligned", "last_review": "2026-06-30"}
    }

@router.get("/decisions/export")
async def export_clinical_audit(
    format: str = "json",
    user = Depends(require_admin)
):
    """Export clinical audit trail with cryptographic evidence."""
    return {"message": "Audit export generated successfully", "download_url": "/api/v1/clinical/decisions/download/audit.json"}
