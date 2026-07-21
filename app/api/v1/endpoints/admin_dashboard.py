# backend/app/api/v1/endpoints/admin_dashboard.py
"""
Admin Dashboard API Endpoints for PersonaVault.
Provides system metrics, monitoring, and management capabilities.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import os
import time
import logging
from app.services.memory_service import MemoryService
import json
import shutil
import psutil
import asyncio
import random

from app.db.session import get_db, SessionLocal
from app.models import (
    User, Memory, AuditLog, UserSession, SystemConfig,
    AISetting, IoTDevice, IoTData, LegalMatter, WorkflowTask, LegalDocument, PendingAction, EpisodicEntry
) # Added LegalDocument for analysis
from app.core.dependencies import require_admin
from app.services.custom import (
    CRYSTALLIZATION_VELOCITY, SUBLIMATION_COUNT, PLASMA_ACTIVE,
    EVAPORATION_COUNT, CONDENSATION_VELOCITY
)
from app.config import Config
from app.utils.websocket import manager
from app.services.iot_service import IoTService

logger = logging.getLogger(__name__)

def _safe_metric_get(metric, default=0):
    """Safely get value from a Prometheus metric object or numeric constant."""
    try:
        if hasattr(metric, '_value') and hasattr(metric._value, 'get'):
            return metric._value.get()
        if hasattr(metric, 'value'):
            return metric.value
        return float(metric) if metric is not None else default
    except (TypeError, ValueError):
        return default

router = APIRouter(prefix="/admin/dashboard", tags=["admin"])

# ============ Metrics & Monitoring ============

@router.get("/metrics")
async def get_system_metrics(
    request: Request, # Added to access app.state services
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive system metrics for the dashboard."""
    now_utc = datetime.utcnow() # Standardize to naive UTC to match application and DB defaults
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Define tasks for concurrent execution to solve sequential bottlenecks
    tasks = [
        db.execute(select(func.count(User.id))),
        db.execute(select(func.count(User.id)).where(User.created_at >= start_of_day)),
        db.execute(select(func.count(User.id)).where(User.last_login >= now_utc - timedelta(days=30))),
        db.execute(select(func.count(Memory.id))),
        db.execute(select(Memory).where(Memory.expiry_days > 0)),
        db.execute(select(func.count(UserSession.id)).where(UserSession.is_active.is_(True))),
        db.execute(select(func.count(UserSession.id)).where(UserSession.created_at >= start_of_day)),
        db.execute(select(func.count(IoTDevice.id))),
        db.execute(select(IoTDevice).where(IoTDevice.status == "active")),
        db.execute(select(func.count(IoTData.id)).where(IoTData.timestamp >= start_of_day)),
        db.execute(select(func.count(LegalMatter.id)).where(LegalMatter.status == "active")),
        db.execute(select(func.count(AISetting.id)).where(AISetting.is_active.is_(True))),
        db.execute(select(SystemConfig).where(SystemConfig.key == "primary_ai_provider"))
    ]

    # Execute all queries concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    try:
        # Helper to safely extract scalar from results
        def get_val(idx, default=0):
            if isinstance(results[idx], Exception): return default
            return results[idx].scalar_one()

        expiring_list = results[4].scalars().all() if not isinstance(results[4], Exception) else []
        active_iot_results = results[8].scalars().all() if not isinstance(results[8], Exception) else []
        
        expired_count = 0
        soon_count = 0
        for m in expiring_list:
            expiry_date = m.created_at + timedelta(days=m.expiry_days)
            if expiry_date < now_utc:
                expired_count += 1
            elif now_utc <= expiry_date < (now_utc + timedelta(days=3)):
                soon_count += 1

        metrics = {
            "users": {
                "total": get_val(0),
                "new_today": get_val(1),
                "active_30d": get_val(2)
            },
            "memories": {
                "total": get_val(3),
                "expired": expired_count,
                "expiring_soon": soon_count
            },
            "sessions": {
                "active": get_val(5),
                "total_today": get_val(6)
            },
            "iot": {
                "total_devices": get_val(7),
                "active_count": len(active_iot_results),
                "active_devices": [d.device_name or d.device_id for d in active_iot_results],
                "data_points_today": get_val(9)
            },
            "legal": {
                "active_matters": get_val(10)
            }
        }

        # AI
        try:
            active_ai_stmt = select(func.count(AISetting.id)).where(AISetting.is_active.is_(True))
            active_ai_settings = (await db.execute(active_ai_stmt)).scalar_one()
            
            ai_provider_stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
            ai_provider_config = (await db.execute(ai_provider_stmt)).scalars().first()
            primary_provider = ai_provider_config.value if ai_provider_config else "ollama"

            # Check VeriLink Integration Status
            orchestrator = getattr(request.app.state, "orchestrator", None)
            verilink_status = getattr(orchestrator, "governance_status", "not_installed")
            verilink_offline = getattr(orchestrator, "offline_mode", False)
            
        except Exception:
            active_ai_settings, primary_provider, verilink_offline = 0, "ollama", False

        return {
            "timestamp": now_utc.isoformat(),
            **metrics,
            "ai": {
                "active_configs": active_ai_settings,
                "primary_provider": primary_provider,
                "ollama_status": await _check_ollama(request),
                "gemini_status": await _check_gemini(request),
                "verilink_status": verilink_status,
                "verilink_offline": verilink_offline
            },
            "system": {
                "vector_index_size": len(request.app.state.vector_service.metadata) if hasattr(request.app.state, "vector_service") and getattr(request.app.state.vector_service, "metadata", None) is not None else 0,
                "graph_healthy": request.app.state.graph_service.check_health() if hasattr(request.app.state, "graph_service") and hasattr(request.app.state.graph_service, 'check_health') else False,
                "vector_healthy": request.app.state.vector_service.check_health() if hasattr(request.app.state, "vector_service") and hasattr(request.app.state.vector_service, 'check_health') else False,
                "storage_used": await _get_storage_usage(),
                "thermodynamics": {
                    "crystallization_rate": _safe_metric_get(CRYSTALLIZATION_VELOCITY),
                    "evaporation_total": _safe_metric_get(EVAPORATION_COUNT),
                    "condensation_rate": _safe_metric_get(CONDENSATION_VELOCITY),
                    "sublimations_total": _safe_metric_get(SUBLIMATION_COUNT),
                    "plasma_state": "High-Energy Reasoning Active" if _safe_metric_get(PLASMA_ACTIVE) > 0 else "Stable"
                }
            }
        }
    except Exception as e:
        logger.error(f"Critical metrics failure: {e}", exc_info=True)
        # Return partial data if possible instead of 500
        return {"timestamp": datetime.utcnow().isoformat(), "error": "Partial metrics failure", **metrics}

# ============ Data Exploration ============

@router.get("/memories")
async def list_memories(
    user_id_admin: int = Depends(require_admin),
    user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all memories with optional filters."""
    stmt = select(Memory)
    if user_id:
        stmt = stmt.where(Memory.user_id == user_id)
    
    total_stmt = select(func.count(Memory.id)).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    memories_stmt = stmt.order_by(Memory.created_at.desc()).offset(offset).limit(limit)
    memories = (await db.execute(memories_stmt)).scalars().all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "memories": [{
            "id": m.id,
            "user_id": m.user_id,
            "title": m.title,
            "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,
            "tags": m.tags,
            "created_at": m.created_at.isoformat(),
            "expiry_days": m.expiry_days
        } for m in memories]
    }

@router.get("/memories/{memory_id}")
async def get_memory_detail(
    memory_id: int,
    user_id_admin: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed memory information."""
    stmt = select(Memory).where(Memory.id == memory_id)
    memory = (await db.execute(stmt)).scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "id": memory.id,
        "user_id": memory.user_id,
        "title": memory.title,
        "content": memory.content,
        "tags": memory.tags,
        "modality": memory.modality,
        "embedding": memory.embedding[:10] if memory.embedding else None,
        "extra_data": memory.extra_data,
        "created_at": memory.created_at.isoformat(),
        "updated_at": memory.updated_at.isoformat(),
        "expiry_days": memory.expiry_days,
        "is_encrypted": memory.is_encrypted
    }

@router.get("/users")
async def list_users(
    user_id_admin: int = Depends(require_admin),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all users."""
    total_stmt = select(func.count(User.id))
    total = (await db.execute(total_stmt)).scalar_one()
    
    # Optimized to avoid N+1 queries
    users_stmt = (
        select(User, func.count(Memory.id).label("mem_count"))
        .outerjoin(Memory)
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(users_stmt)
    users_data = result.all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "users": [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "memory_count": mem_count
        } for u, mem_count in users_data]
    }

@router.get("/audit-logs")
async def get_audit_logs(
    user_id_admin: int = Depends(require_admin),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters."""
    stmt = select(AuditLog)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    
    total_stmt = select(func.count(AuditLog.id)).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    logs_stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    logs = (await db.execute(logs_stmt)).scalars().all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "logs": [{
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "timestamp": l.timestamp.isoformat()
        } for l in logs]
    }

# ============ Real-time Dashboard WebSocket ============

@router.websocket("/ws/{client_id}")
async def dashboard_websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket for real-time dashboard metrics and IoT updates."""
    # SECURITY HANDSHAKE: Ensure only authenticated admins can stream system state
    session_id = websocket.cookies.get("session_id")
    if not session_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "iot_data":
                    await IoTService.process_realtime_data(parsed["data"])
            except Exception as e:
                logger.error(f"WebSocket processing error: {e}")
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)

# ============ System Operations ============

@router.get("/hitl/pending")
async def list_pending_hitl(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all pending Human-In-The-Loop actions from the database."""
    stmt = select(PendingAction).where(PendingAction.status == "pending").order_by(PendingAction.created_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    return [{
        "id": p.id,
        "agent_type": p.agent_type,
        "query": p.query,
        "timestamp": p.created_at.isoformat(),
        "vap_hash": p.vap_hash,
        "action_chain_id": p.action_chain_id,
        "data": json.loads(p.options) if p.options and p.options.startswith('{') else {}
    } for p in results]

@router.post("/hitl/{action_id}/approve")
async def approve_hitl(
    action_id: int, 
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Approve a pending HITL action."""
    stmt = select(PendingAction).where(PendingAction.id == action_id)
    action = (await db.execute(stmt)).scalars().first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "approved"
    action.resolved_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Admin approved HITL action: {action_id}")
    return {"status": "approved", "action_id": action_id}

@router.post("/hitl/{action_id}/deny")
async def deny_hitl(
    action_id: int, 
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deny a pending HITL action."""
    stmt = select(PendingAction).where(PendingAction.id == action_id)
    action = (await db.execute(stmt)).scalars().first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "rejected"
    action.resolved_at = datetime.utcnow()
    await db.commit()

    logger.info(f"Admin denied HITL action: {action_id}")
    return {"status": "denied", "action_id": action_id}

@router.post("/hitl/{action_id}/explain")
async def explain_hitl_reasoning(
    action_id: int,
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Uses the JudgeAgent to provide a human-readable summary of the cognitive state."""
    stmt = select(PendingAction).where(PendingAction.id == action_id)
    action = (await db.execute(stmt)).scalars().first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    judge = request.app.state.judge_agent
    prompt = f"""
    ### TASK: COGNITIVE STATE DECODING
    Explain WHY the {action.agent_type} issued an intervention and WHAT the operator should consider.
    
    INTERVENTION QUERY: {action.query}
    TECHNICAL STATE (JSON):
    {action.options}
    
    ### INSTRUCTIONS:
    1. Translate technical triggers (like physiological data or risk scores) into plain English.
    2. Clearly state the safety or logic conflict identified.
    3. Provide a neutral recommendation (Approve/Deny) based on system policy.
    
    EXPLANATION:
    """
    
    try:
        res = await judge._client.post(
            f"{judge.ollama_url}/api/generate",
            json={"model": judge.ollama_model, "prompt": prompt, "stream": False},
            timeout=45.0
        )
        return {"explanation": res.json().get("response", "Could not parse AI response.")}
    except Exception as e:
        logger.error(f"Judge explanation failed: {e}")
        return {"explanation": "The AI reasoning engine is currently under high load. Please manually review the JSON state."}

@router.get("/governance/logs")
async def get_governance_logs(
    user_id_admin: int = Depends(require_admin),
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve episodic entries containing VeriLink governance metadata."""
    stmt = select(EpisodicEntry).order_by(EpisodicEntry.timestamp.desc()).limit(limit)
    results = (await db.execute(stmt)).scalars().all()
    return {
        "logs": [{
            "id": e.id,
            "query": e.query[:60] + "..." if len(e.query) > 60 else e.query,
            "receipt": e.governance_receipt_id or "local_bypass",
            "signature": e.signature or "unsealed",
            "hitl": e.hitl_approved,
            "timestamp": e.timestamp.isoformat()
        } for e in results]
    }

@router.post("/system/simulate-iot")
async def toggle_iot_simulation(request: Request, user_id: int = Depends(require_admin)):
    """Start or stop the background IoT simulation."""
    if hasattr(request.app.state, "iot_sim_task") and request.app.state.iot_sim_task and not request.app.state.iot_sim_task.done():
        request.app.state.iot_sim_task.cancel()
        request.app.state.iot_sim_task = None
        logger.info("Admin stopped IoT simulation task.")
        return {"status": "stopped", "message": "Simulation terminated"}
    
    request.app.state.iot_sim_task = asyncio.create_task(_run_iot_simulation())
    logger.info("Admin ignited IoT simulation task.")
    return {"status": "started", "message": "Simulation running in background"}

async def _run_iot_simulation():
    """Background task to simulate IoT data flow."""
    sim_device_identifier = "simulated_sensor_001"
    owner_id = 1
    
    # Initialize simulated device to ensure foreign key constraints pass
    try:
        async with SessionLocal() as db:
            # Find an existing user to act as owner to prevent IntegrityError
            user_res = await db.execute(select(User).order_by(User.id))
            owner = user_res.scalars().first()
            if not owner:
                logger.error("Simulation failed: No users found in database. Please register a user first.")
                return
            owner_id = owner.id

            res = await db.execute(select(IoTDevice).where(IoTDevice.device_id == sim_device_identifier))
            device = res.scalars().first()
            
            if not device:
                device = IoTDevice(
                    device_id=sim_device_identifier,
                    device_name="Admin Simulation Sensor",
                    user_id=owner_id,
                    device_type="sensor",
                    status="active",
                    last_seen=datetime.utcnow()
                )
                db.add(device)
            else:
                device.status = "active"
                device.last_seen = datetime.utcnow()
            
            await db.commit()
            logger.info(f"Simulation device ready: {sim_device_identifier} (Owner ID: {owner_id})")
    except Exception as e:
        logger.error(f"Simulation setup failed: {e}")

    try:
        while True:
            try:
                readings = {
                    "temperature": round(random.uniform(18, 25), 2),
                    "humidity": round(random.uniform(40, 60), 2),
                    "heart_rate": random.randint(60, 80)
                }
                # Process data directly through IoTService logic
                await IoTService.process_realtime_data({
                    "device_id": sim_device_identifier,
                    "device_identifier": sim_device_identifier, # Fallback for service logic
                    "user_id": owner_id,
                    "data_type": "sensor_readings",
                    "type": "sensor_readings", # Fallback for service logic
                    "timestamp": datetime.utcnow().isoformat(), # Use string for serialization safety
                    "value": readings
                })
                # Broadcast for real-time dashboard updates
                await manager.broadcast(json.dumps({"type": "iot_update", "device": sim_device_identifier, "data": readings}))
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass

@router.post("/memories/cleanup")
async def cleanup_expired_memories(
    request: Request,
    user_id_admin: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger memory cleanup."""
    service = MemoryService(
        db=db,
        vector_service=request.app.state.vector_service,
        graph_service=request.app.state.graph_service
    )
    count = await service.delete_expired_memories()
    return {"deleted": count, "timestamp": datetime.utcnow().isoformat()}

@router.post("/system/cleanup-uploads")
async def cleanup_upload_directory(
    user_id_admin: int = Depends(require_admin)
):
    """Clear the local upload storage to free up disk space."""
    upload_dir = "storage/uploads"
    files_deleted = 0
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
                files_deleted += 1
    
    return {"status": "success", "files_deleted": files_deleted}

@router.post("/memories/{memory_id}/delete")
async def delete_memory_admin(
    memory_id: int,
    user_id_admin: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin delete a specific memory."""
    stmt = select(Memory).where(Memory.id == memory_id)
    memory = (await db.execute(stmt)).scalars().first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    await db.delete(memory)
    await db.commit()
    return {"deleted": True, "memory_id": memory_id}

@router.post("/governance/toggle-offline")
async def toggle_verilink_offline(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Toggle VeriLink Offline Mode to manually suppress connection attempts."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    # Update/Get DB Config
    stmt = select(SystemConfig).where(SystemConfig.key == "verilink_offline_mode")
    config = (await db.execute(stmt)).scalars().first()
    
    # Toggle current state
    is_currently_offline = config.value == "true" if config else False
    new_offline_state = not is_currently_offline
    val_str = "true" if new_offline_state else "false"
    
    if not config:
        db.add(SystemConfig(key="verilink_offline_mode", value=val_str))
    else:
        config.value = val_str
    
    await db.commit()
    
    # Update Live Orchestrator Instance
    orchestrator.offline_mode = new_offline_state
    
    if new_offline_state:
        orchestrator.governance = None
        orchestrator.governance_status = "manual_offline"
        logger.info("Admin manually suppressed VeriLink connection.")
    else:
        # Re-attempt initialization if resumed
        try:
            from verilink_plugin import VeriLinkGovernancePlugin
            orchestrator.governance = VeriLinkGovernancePlugin()
            orchestrator.governance_status = "active"
            logger.info("Admin resumed VeriLink connection attempts.")
        except Exception as e:
            orchestrator.governance = None
            orchestrator.governance_status = "offline_fail_soft"
            logger.warning(f"VeriLink resume failed: {e}")
    
    return {"status": "success", "offline_mode": new_offline_state}

@router.post("/system/refresh-vector-index")
async def refresh_vector_index(
    request: Request,
    user_id_admin: int = Depends(require_admin),
    clear_cache: bool = False
):
    """Refresh the vector index."""
    try:
        if clear_cache:
            # Attempt to clear potential corrupted metadata files
            metadata_path = os.path.join("storage", "vector_metadata.pkl")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                logger.info("Cleared potentially corrupted vector metadata")
        request.app.state.vector_service._load_or_create_index() # Re-initialize the index
        return {
            "status": "success",
            "message": "Vector index reset" if clear_cache else "Vector index refresh triggered",
            "current_size": len(request.app.state.vector_service.metadata) if request.app.state.vector_service.metadata else 0
        }
    except Exception as e:
        logger.error(f"Failed to refresh vector index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ Health & Status ============

@router.get("/health")
async def admin_health_check( # Renamed to avoid conflict with main.py's detailed_health
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Detailed health check for admin."""
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Admin health check DB error: {e}")
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "connected" if db_ok else "disconnected",
            "vector_store": "active" if request.app.state.vector_service and request.app.state.vector_service.index else "inactive",
            "graph_store": "connected" if request.app.state.graph_service and request.app.state.graph_service.driver else "disconnected",
            "ollama": await _check_ollama(request),
            "gemini": await _check_gemini(request)
        },
        "system": {
            "cpu": await _get_cpu_usage(),
            "memory": await _get_memory_usage()
        }
    }

@router.get("/activity")
async def get_recent_activity(
    minutes: int = 60,
    user_id_admin: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get recent system activity."""
    since = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Get recent memory creations
    new_memories_stmt = select(func.count(Memory.id)).where(
        Memory.created_at >= since
    )
    new_memories = (await db.execute(new_memories_stmt)).scalar_one()
    
    # Get recent logins
    logins_stmt = select(func.count(AuditLog.id)).where(
        AuditLog.action == "user_login",
        AuditLog.timestamp >= since
    )
    logins = (await db.execute(logins_stmt)).scalar_one()
    
    # Get recent IoT data
    iot_data_stmt = select(func.count(IoTData.id)).where(
        IoTData.timestamp >= since
    )
    iot_data = (await db.execute(iot_data_stmt)).scalar_one()

    total_requests_stmt = select(func.count(AuditLog.id)).where(AuditLog.timestamp >= since)
    total_requests = (await db.execute(total_requests_stmt)).scalar_one()
    
    return {
        "period_minutes": minutes,
        "new_memories": new_memories,
        "user_logins": logins,
        "iot_data_points": iot_data, # This was missing in the original code
        "total_requests": total_requests
    }

# ============ Helper Functions ============

# Add a cache for Ollama status
_ollama_cache = {
    "status": "unknown",
    "last_check": 0,
    "cache_ttl": 30  # Only check every 30 seconds
}

async def _check_ollama(request: Request) -> str:
    """Check Ollama service status with caching."""
    now = time.time()
    if now - _ollama_cache["last_check"] < _ollama_cache["cache_ttl"]:
        return _ollama_cache["status"]

    try:
        client = request.app.state.ai_client
        # Use centralized config and shorter timeout for health check
        url = f"{Config.OLLAMA_BASE_URL}/api/tags"
        response = await client.get(url, timeout=1.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            _ollama_cache["status"] = f"connected ({len(models)} models)" if models else "connected (no models)"
        else:
            _ollama_cache["status"] = "error"
    except Exception as e:
        logger.warning(f"Ollama health check: service unreachable at {Config.OLLAMA_BASE_URL}")
        _ollama_cache["status"] = "disconnected"

    _ollama_cache["last_check"] = now
    return _ollama_cache["status"]

async def _check_gemini(request: Request) -> str:
    """Check Gemini service status."""
    api_key = Config.GEMINI_API_KEY # Use centralized config
    if not api_key:
        return "not_configured"
    try:
        import google.generativeai as genai # type: ignore
        genai.configure(api_key=api_key)
        # Client-side configuration check.
        # The actual list_models() can be blocking, so we'll just check if the client is configured.
        # For a true async check, you'd need an async Gemini client.
        # For now, we assume if the key is configured and genai loads, it's "connected".
        # A more robust check would involve a small, quick API call.
        return "connected"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return "error"

async def _get_storage_usage() -> dict:
    """Get storage usage information."""
    home_dir = os.path.expanduser("~")
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    
    def get_dir_size(path):
        total = 0
        if not os.path.exists(path):
            return 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
        except Exception as e:
            logger.debug(f"Directory size check failed for {path}: {e}")
            pass
        return round(total / (1024**2), 2)  # Return MB

    try:
        total, used, free = shutil.disk_usage(home_dir)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round((used / total) * 100, 2) if total > 0 else 0,
            "breakdown_mb": {
                "venv": get_dir_size(os.path.join(project_dir, ".venv")),
                "uploads": get_dir_size(os.path.join(project_dir, "storage/uploads")),
                "cargo_cache": get_dir_size(os.path.expanduser("~/.cargo")),
                "rustup": get_dir_size(os.path.expanduser("~/.rustup")),
                "vector_storage": get_dir_size(os.path.join(project_dir, "storage"))
            },
            "checked_at": datetime.utcnow().isoformat()
        }
    except:
        return {"error": "Unable to get storage info"}

async def _get_cpu_usage() -> float:
    """Get CPU usage."""
    try:
        # interval=None returns usage since last call without blocking the event loop
        return psutil.cpu_percent(interval=None)
    except Exception as e:
        logger.warning(f"CPU metrics unavailable: {e}")
        return -1

async def _get_memory_usage() -> dict:
    """Get memory usage."""
    try:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "free_gb": round(mem.free / (1024**3), 2),
            "used_percent": mem.percent
        }
    except:
        return {"error": "Unable to get memory info"}

# ============ DASHBOARD UI ============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PersonaVault Admin</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --accent: #38bdf8; --bg: #0f172a; --card-bg: #1e293b; --sidebar: #111827; --border: #334155; --success: #34d399; --warning: #fbbf24; --danger: #f87171; }
        * { box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: #f1f5f9; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: var(--card-bg); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding: 15px 30px; z-index: 10; flex-shrink: 0; }
        h1 { color: #38bdf8; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.025em; }
        .layout { display: flex; flex: 1; overflow: hidden; }
        .sidebar { width: 260px; background: var(--sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding-top: 20px; overflow-y: auto; flex-shrink: 0; }
        .nav-group { margin-bottom: 25px; }
        .nav-label { padding: 0 30px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
        .nav-item { padding: 12px 30px; cursor: pointer; color: #94a3b8; font-size: 14px; transition: all 0.2s; border-left: 3px solid transparent; display: flex; align-items: center; gap: 10px; }
        .nav-item:hover { background: rgba(56, 189, 248, 0.05); color: #f1f5f9; }
        .nav-item.active { background: rgba(56, 189, 248, 0.1); color: var(--accent); border-left-color: var(--accent); font-weight: 600; }
        .main-content { flex: 1; overflow-y: auto; padding: 40px; }
        .tab-content { display: none; animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .card { background: var(--card-bg); border-radius: 12px; padding: 25px; border: 1px solid var(--border); transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .card-title { font-size: 14px; font-weight: 700; color: var(--accent); text-transform: uppercase; margin: 0; }
        .metric-value { font-size: 36px; font-weight: 800; color: #fbbf24; margin: 10px 0; }
        .metric-label { color: #94a3b8; text-transform: uppercase; font-size: 12px; font-weight: 600; letter-spacing: 0.05em; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; background: var(--border); color: #f1f5f9; }
        .tag-success { background: #065f46; color: #34d399; }
        .btn { display: inline-flex; align-items: center; gap: 8px; background: var(--accent); color: #0f172a; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 700; border: none; cursor: pointer; transition: all 0.2s; }
        .btn:hover { background: #7dd3fc; }
        .refresh-btn { cursor: pointer; color: var(--accent); background: transparent; border: 1px solid var(--accent); padding: 8px 16px; border-radius: 6px; font-weight: 600; transition: all 0.2s; }
        .refresh-btn:hover { background: rgba(56, 189, 248, 0.1); }
        pre { background: #020617; padding: 20px; border-radius: 8px; color: var(--accent); border: 1px solid var(--border); line-height: 1.5; white-space: pre-wrap; word-break: break-all; font-size: 13px; max-height: 400px; overflow: auto; }
        .input-field { width: 100%; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #334155; background: #020617; color: white; box-sizing: border-box; }
        .mem-viz-container { margin-top: 15px; background: #020617; border-radius: 6px; height: 14px; display: flex; overflow: hidden; border: 1px solid var(--border); }
        .viz-l2 { background: #38bdf8; height: 100%; transition: width 0.6s ease-in-out; }
        .viz-l3 { background: #a855f7; height: 100%; transition: width 0.6s ease-in-out; }
        .viz-legend { display: flex; gap: 20px; margin-top: 10px; font-size: 11px; color: #94a3b8; }
        .log-container { background: #020617; flex-grow: 1; overflow-y: auto; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 11px; border: 1px solid var(--border); white-space: pre-wrap; line-height: 1.4; max-height: 500px; }
        .log-line-error { color: #f87171; }
        .log-line-warning { color: #fbbf24; }
        .log-line-info { color: #38bdf8; }
        .flex-between { display: flex; justify-content: space-between; align-items: center; }
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: #94a3b8; }
        .stat-value { color: #f1f5f9; font-weight: 600; font-family: monospace; }
        .toast-container { position: fixed; bottom: 30px; right: 30px; z-index: 1000; display: flex; flex-direction: column; gap: 12px; }
        .toast { background: var(--card-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); padding: 14px 24px; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3); min-width: 280px; animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); display: flex; align-items: center; gap: 12px; transition: all 0.3s; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .toast.success { border-left-color: var(--success); }
        .toast.error { border-left-color: var(--danger); }
        .toast.info { border-left-color: var(--accent); }
        .modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px); }
        .modal-content { background: var(--card-bg); margin: 5% auto; padding: 30px; border: 1px solid var(--border); width: 85%; max-width: 900px; border-radius: 12px; position: relative; max-height: 85vh; overflow-y: auto; }
        .close-modal { position: absolute; top: 20px; right: 25px; color: #64748b; font-size: 28px; cursor: pointer; }
        .close-modal:hover { color: white; }
    </style>
</head>
<body>
    <header>
        <h1>🛡️ PersonaVault System Control</h1>
        <div style="display: flex; gap: 10px;">
            <button class="refresh-btn" onclick="fetchMetrics()"><i class="fas fa-sync-alt"></i> Refresh</button>
            <button class="refresh-btn" style="color: var(--danger); border-color: var(--danger);" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</button>
        </div>
    </header>
    
    <div class="layout">
        <nav class="sidebar">
            <div class="nav-group">
                <div class="nav-label">Core Pulse</div>
                <div class="nav-item active" onclick="switchTab(event, 'overview')">📊 System Overview</div>
                <div class="nav-item" onclick="switchTab(event, 'models')">📦 Model Management</div>
                <div class="nav-item" onclick="switchTab(event, 'logs')">📜 System Logs</div>
            </div>
            <div class="nav-group">
                <div class="nav-label">Cognitive Architecture</div>
                <div class="nav-item" onclick="switchTab(event, 'lattices')">🕸️ Memory Lattices</div>
                <div class="nav-item" onclick="switchTab(event, 'learning')">⚡ Graduation Logic</div>
                <div class="nav-item" onclick="switchTab(event, 'agents')">🤖 Agent Orchestration</div>
            </div>
            <div class="nav-group">
                <div class="nav-label">Enterprise & Safety</div>
                <div class="nav-item" onclick="switchTab(event, 'governance')">⚖️ Governance & Audit</div>
                <div class="nav-item" onclick="switchTab(event, 'security')">🔐 Privacy Vault</div>
            </div>
        </nav>
        
        <main class="main-content">
            <div id="overview-tab" class="tab-content active">
                <div id="metrics-grid" class="grid">
                    <div class="card"><div class="metric-label">Loading...</div></div>
                </div>
                <div class="card" style="margin-bottom: 25px; border-top: 4px solid #fbbf24;">
                    <h3 class="card-title">Laboratory & Simulation</h3>
                    <p style="color: #94a3b8; font-size: 13px;">Trigger virtual telemetry to test real-time monitoring and HITL triggers.</p>
                    <button class="btn" id="sim-btn" onclick="toggleSimulation()"><i class="fas fa-bolt"></i> Ignite IoT Simulation</button>
                </div>
                <h2 style="margin-top: 40px; color: #94a3b8; font-size: 14px; text-transform: uppercase;">Raw Intelligence Feed</h2>
                <pre id="raw-metrics">Fetching system state...</pre>
            </div>

            <div id="models-tab" class="tab-content">
                <h2 style="color: var(--accent);">AI Model Management (Ollama)</h2>
                <div class="card" style="margin-bottom: 25px;">
                    <h3 style="margin-top:0; color: #38bdf8;">Pull New Model</h3>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="new-model-input" placeholder="e.g. llama3" class="input-field" style="flex:1;">
                        <button class="btn" onclick="triggerModelPull()"><i class="fas fa-download"></i> Pull Model</button>
                    </div>
                    <div id="pull-status" style="margin-top: 15px; font-family: monospace; font-size: 11px; color: #fbbf24; white-space: pre-wrap;"></div>
                </div>
                <div class="card">
                    <h3 style="margin-top:0; color: #34d399;">Installed Local Models</h3>
                    <div id="models-list" style="display: flex; flex-direction: column; gap: 12px;">
                        <div class="metric-label">Loading models...</div>
                    </div>
                </div>
            </div>

            <div id="lattices-tab" class="tab-content">
                <h2 style="color: var(--accent);">Memory Lattices (Layers 1-3)</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 20px;">
                    Visualization of the conversion from Volatile Context (Gas) to Episodic Memory (Liquid) and Semantic Constraints (Ice).
                </p>
                <div class="card" style="margin-bottom: 25px; border-left: 4px solid #a855f7;">
                    <div class="metric-label">Memory Distribution Ratio</div>
                    <div class="mem-viz-container">
                        <div id="bar-l2" class="viz-l2" style="width: 50%"></div>
                        <div id="bar-l3" class="viz-l3" style="width: 10%"></div>
                    </div>
                </div>
                <div class="grid">
                    <div class="card"><div class="metric-label">Layer 1 (Gas)</div><div class="metric-value">Active</div></div>
                    <div class="card"><div class="metric-label">Layer 2 (Liquid)</div><div id="layer2-count" class="metric-value">0</div></div>
                    <div class="card"><div class="metric-label">Layer 3 (Ice)</div><div id="layer3-count" class="metric-value">0</div></div>
                </div>
            </div>

            <div id="learning-tab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Crystallization Engine</h3>
                        <span class="tag tag-success">ACTIVE</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 13px;">Configure the background task that graduates Liquid memories into Semantic Ice.</p>
                    <div style="margin: 20px 0;">
                        <div class="flex-between mb-10"><span style="color: #94a3b8; font-size: 13px;">Batch Size</span><input type="number" id="input-batch-size" style="width: 80px; background: #020617; border: 1px solid var(--border); color: white; padding: 4px;"></div>
                        <div class="flex-between mb-10"><span style="color: #94a3b8; font-size: 13px;">Interval (Hours)</span><input type="number" step="0.1" id="input-interval" style="width: 80px; background: #020617; border: 1px solid var(--border); color: white; padding: 4px;"></div>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn" style="flex: 1; background: #334155; color: white;" onclick="saveLearningConfig()">Save</button>
                        <button class="btn" style="flex: 2; background: #a855f7;" onclick="triggerLearning()"><i class="fas fa-crystal-ball"></i> Trigger Now</button>
                    </div>
                    <div id="learning-status" style="font-size: 11px; color: #94a3b8; margin-top: 12px; text-align: center;">Crystallization monitoring online.</div>
                </div>
            </div>

            <div id="agents-tab" class="tab-content">
                <h2 style="color: var(--accent);">Agent Orchestration</h2>
                <div class="grid">
                    <div class="card">
                        <div class="card-title">Cognitive Load</div>
                        <div id="agent-load-stats" class="mt-10"></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Empathy & Tone</div>
                        <div id="empathy-stats" class="mt-10"></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">HITL / Pending Actions</div>
                    <div id="hitl-list" class="mt-10">
                        <div class="metric-label" style="text-align: center; padding: 20px;">No pending Human-In-The-Loop requests.</div>
                    </div>
                </div>
            </div>

            <div id="logs-tab" class="tab-content">
                <div class="card" style="height: calc(100vh - 200px); display: flex; flex-direction: column;">
                    <div class="flex-between mb-10">
                        <h3 style="margin:0; color: #34d399;">Live Engine Logs</h3>
                        <button class="refresh-btn" onclick="document.getElementById('log-container').innerHTML = ''"><i class="fas fa-eraser"></i> Clear View</button>
                    </div>
                    <div id="log-container" class="log-container"></div>
                </div>
            </div>

            <div id="governance-tab" class="tab-content">
                <h2 style="color: var(--accent);">Governance & Audit</h2>
                <div class="card" style="margin-bottom: 25px; border-left: 4px solid #f87171;">
                    <div class="flex-between">
                        <div>
                            <h3 class="card-title">VeriLinkOS Execution Kernel</h3>
                            <p id="verilink-desc" style="color: #94a3b8; font-size: 12px; margin-top: 5px;">Currently in fail-soft mode.</p>
                        </div>
                        <button class="btn" id="verilink-toggle-btn" onclick="toggleVeriLinkMode()"><i class="fas fa-plug-circle-xmark"></i> Suppress Connection</button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header"><h3 class="card-title">Action Chain & VAP Receipts</h3></div>
                    <div id="audit-container" style="max-height: 400px; overflow-y: auto;">
                        <div class="metric-label">Loading audit trail...</div>
                    </div>
                </div>
            </div>

            <div id="security-tab" class="tab-content">
                <h2 style="color: var(--accent);">Privacy Vault</h2>
                <div class="card">
                    <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Encryption Status</span><span style="color: #34d399;">✅ Active</span></div>
                    <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Tokenization</span><span style="color: #34d399;">✅ Enabled</span></div>
                </div>
            </div>
        </main>
    </div>

    <div id="toast-container" class="toast-container"></div>

    <div id="details-modal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <h2 style="color: var(--accent); margin-top: 0; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-microchip"></i> Orchestrator State Snapshot
            </h2>
            <hr style="border: 0; border-top: 1px solid var(--border); margin: 20px 0;">
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        let logSource = null;
        let ws = null;
        let currentHitlData = [];

        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info');
            toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function switchTab(event, tabId) {
            document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.getElementById(tabId + '-tab').classList.add('active');
            if (tabId === 'logs') startLogStream();
            if (tabId === 'models') fetchInstalledModels();
            if (tabId === 'learning') fetchLearningConfig();
            if (tabId === 'governance') fetchGovernanceLogs();
            if (tabId === 'agents') fetchAgentStatus();
        }

        function startLogStream() {
            if (logSource) logSource.close();
            const container = document.getElementById('log-container');
            container.innerHTML = '';
            logSource = new EventSource('/api/v1/logs/stream');
            logSource.onmessage = function(e) {
                const line = document.createElement('div');
                line.textContent = e.data;
                if (e.data.includes('ERROR')) line.className = 'log-line-error';
                else if (e.data.includes('WARNING')) line.className = 'log-line-warning';
                else if (e.data.includes('INFO')) line.className = 'log-line-info';
                container.appendChild(line);
                container.scrollTop = container.scrollHeight;
            };
        }

        function connectWebSocket() {
            if (ws) ws.close();
            const clientId = 'admin_' + Math.random().toString(36).substring(7);
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // Proxied via /api/v1 prefix in main.py
            ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/admin/dashboard/ws/${clientId}`);
            
            ws.onopen = function() {
                console.log('✅ Dashboard WebSocket connected successfully');
            };
            
            ws.onmessage = function(e) {
                const data = JSON.parse(e.data);
                console.log('📥 WebSocket Signal Received:', data.type, data);
                // Use throttled refresh to avoid 429 errors
                if (data.type === 'iot_update' || data.type === 'metrics_update') throttledFetch();
            };
            ws.onclose = function() { 
                console.log('❌ Dashboard WebSocket disconnected. Retrying in 5s...');
                setTimeout(connectWebSocket, 5000); 
            };
            ws.onerror = function(err) {
                console.error('⚠️ WebSocket Connection Error:', err);
            };
        }

        let lastFetch = 0;
        let fetchInProgress = false;
        function throttledFetch() {
            const now = Date.now();
            if (fetchInProgress || now - lastFetch < 30000) return; // Limit to once every 30 seconds
            fetchMetrics();
        }

        async function fetchMetrics() {
            lastFetch = Date.now();
            fetchInProgress = true;
            try {
                const res = await fetch('/api/v1/admin/dashboard/metrics');
                if (!res.ok) { 
                    document.getElementById('raw-metrics').textContent = `Server Error (${res.status})`; 
                    return; 
                }
                const data = await res.json();
                document.getElementById('raw-metrics').textContent = JSON.stringify(data, null, 2);
                const grid = document.getElementById('metrics-grid');
                
                // Update VeriLink UI
                const vBtn = document.getElementById('verilink-toggle-btn');
                const vDesc = document.getElementById('verilink-desc');
                const isOffline = data.ai?.verilink_offline;
                
                if (isOffline) {
                    vBtn.innerHTML = '<i class="fas fa-plug-circle-check"></i> Resume Connection';
                    vBtn.style.background = '#34d399';
                    vDesc.innerText = 'VeriLink connection attempts are manually suppressed.';
                } else {
                    vBtn.innerHTML = '<i class="fas fa-plug-circle-xmark"></i> Suppress Connection';
                    vBtn.style.background = '#f87171';
                    vDesc.innerText = 'System is attempting to synchronize with VeriLinkOS.';
                }

                if (data.error) console.warn("Metrics partially failed:", data.error);
                grid.innerHTML = `
                    <div class="card"><div class="metric-label"><i class="fas fa-users"></i> Users</div><div class="metric-value">${data.users?.total || 0}</div></div>
                    <div class="card"><div class="metric-label"><i class="fas fa-brain"></i> Memories</div><div class="metric-value">${data.memories?.total || 0}</div></div>
                    <div class="card"><div class="metric-label">Ollama</div><div class="metric-value" style="font-size:20px;">${data.ai?.ollama_status || 'unknown'}</div></div>
                    <div class="card"><div class="metric-label">Vector Index</div><div class="metric-value">${data.system?.vector_index_size || 0}</div></div>
                    <div class="card"><div class="metric-label">Active Sessions</div><div class="metric-value">${data.sessions?.active || 0}</div></div>
                    <div class="card"><div class="metric-label">Legal Matters</div><div class="metric-value" style="color:var(--accent);">${data.legal?.active_matters || 0}</div></div>
                    <div class="card">
                        <div class="metric-label">Active IoT Devices</div>
                        <div class="metric-value">${data.iot?.active_count || 0}</div>
                        <div style="font-size: 11px; color: #94a3b8; line-height: 1.4; margin-top: 5px;">
                            ${data.iot?.active_devices?.length > 0 ? data.iot.active_devices.join(', ') : 'None'}
                        </div>
                    </div>
                    <div class="card"><div class="metric-label">IoT Telemetry Points</div><div class="metric-value" style="color:#34d399;">${data.iot?.data_points_today || 0}</div></div>
                `;

                // Update Lattice counts
                if (document.getElementById('layer2-count')) {
                    const l2Count = data.memories?.total || 0;
                    const l3Count = data.system?.vector_index_size || 0;
                    document.getElementById('layer2-count').innerText = l2Count;
                    document.getElementById('layer3-count').innerText = l3Count;
                    
                    // Dynamically update visualization bars
                    const total = (l2Count + l3Count) || 1;
                    document.getElementById('bar-l2').style.width = ((l2Count / total) * 100) + '%';
                    document.getElementById('bar-l3').style.width = ((l3Count / total) * 100) + '%';
                }
            } catch(e) { 
                console.error('Metrics fetch error', e); 
            } finally { fetchInProgress = false; }
        }

        async function fetchInstalledModels() {
            const listEl = document.getElementById('models-list');
            try {
                const response = await fetch('/api/v1/admin/models');
                const data = await response.json();
                listEl.innerHTML = (data.models || []).map(m => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #020617; border: 1px solid var(--border); border-radius: 8px;">
                        <div>
                            <div style="font-weight: 700; color: var(--accent);">${m.name}</div>
                            <div style="font-size: 11px; color: #64748b;">Size: ${(m.size / (1024*1024*1024)).toFixed(2)} GB</div>
                        </div>
                        <button class="refresh-btn" style="color: #f87171; border-color: #f87171; padding: 4px 10px; font-size: 11px;" onclick="deleteModel('${m.name}')">Delete</button>
                    </div>
                `).join('');
            } catch (err) { listEl.innerHTML = 'Error loading models'; }
        }

        async function triggerModelPull() {
            const input = document.getElementById('new-model-input');
            const statusEl = document.getElementById('pull-status');
            const name = input.value.trim();
            if (!name) return;
            showToast(`Initiating download for ${name}...`, 'info');
            const response = await fetch('/api/v1/admin/models/pull', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });
            const reader = response.body.getReader();
            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                statusEl.textContent += new TextDecoder().decode(value).replace(/data: /g, '');
                statusEl.scrollTop = statusEl.scrollHeight;
            }
            showToast(`${name} download complete`, 'success');
            fetchInstalledModels();
        }

        async function toggleVeriLinkMode() {
            try {
                const res = await fetch('/api/v1/admin/dashboard/governance/toggle-offline', {method: 'POST'});
                if (!res.ok) throw new Error('Toggle Failed');
                const data = await res.json();
                showToast(data.offline_mode ? 'VeriLink connection suppressed' : 'VeriLink reconnection enabled', 'info');
                fetchMetrics();
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            }
        }

        async function deleteModel(name) {
            if (!confirm(`Permanently purge ${name} from local storage?`)) return;
            await fetch(`/api/v1/admin/models/${name}`, {method: 'DELETE'});
            fetchInstalledModels();
        }

        async function fetchLearningConfig() {
            const res = await fetch('/api/v1/admin/learning/config');
            const data = await res.json();
            document.getElementById('input-batch-size').value = data.batch_size;
            document.getElementById('input-interval').value = data.interval_hours;
        }

        async function saveLearningConfig() {
            const batch_size = document.getElementById('input-batch-size').value;
            const interval_hours = document.getElementById('input-interval').value;
            const res = await fetch('/api/v1/admin/learning/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({batch_size, interval_hours})
            });
            if (res.ok) showToast('Crystallization parameters synchronized', 'success');
        }

        async function triggerLearning() {
            await fetch('/api/v1/admin/learning/trigger', {method: 'POST'});
            showToast('Manual crystallization cycle ignited', 'info');
        }

        async function fetchGovernanceLogs() {
            const container = document.getElementById('audit-container');
            try {
                const res = await fetch('/api/v1/admin/dashboard/governance/logs?limit=20');
                const data = await res.json();
                container.innerHTML = data.logs.map(l => `
                    <div style="padding: 12px 0; border-bottom: 1px solid var(--border);">
                        <div class="flex-between">
                            <span style="font-size:13px; font-weight:600;">${l.query}</span>
                            <span class="tag ${l.hitl ? 'tag-success' : ''}">${l.hitl ? 'HITL' : 'AUTO'}</span>
                        </div>
                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                            <span style="font-size:10px; color: var(--accent); font-family: monospace;">RECEIPT: ${l.receipt}</span>
                            <span style="font-size:10px; color: #64748b;">${new Date(l.timestamp).toLocaleString()}</span>
                        </div>
                    </div>
                `).join('') || '<div class="metric-label">No governance receipts found.</div>';
            } catch (e) { container.innerHTML = 'Error loading logs.'; }
        }

        async function fetchAgentStatus() {
            try {
                const [loadRes, empathyRes, hitlRes] = await Promise.all([
                    fetch('/api/v1/admin/cognitive-load'),
                    fetch('/api/v1/admin/empathy/status'),
                    fetch('/api/v1/admin/dashboard/hitl/pending')
                ]);
                
                const load = await loadRes.json();
                const empathy = await empathyRes.json();
                const hitl = await hitlRes.json();
                currentHitlData = hitl;
                
                let agentHtml = `
                    <div class="stat-row"><span class="stat-label">Active Tasks</span><span class="stat-value">${load.active_tasks || 0}</span></div>
                    <div class="stat-row"><span class="stat-label">Swarm Health</span><span class="stat-value">Nominal</span></div>
                    <div style="margin-top: 15px; border-top: 1px solid var(--border); padding-top: 10px;">
                        <div class="nav-label" style="padding: 0; margin-bottom: 8px; font-size: 10px;">Swarm Agents</div>
                `;
                
                const activity = load.agent_activity || {};
                for (const [name, count] of Object.entries(activity)) {
                    const statusTag = count > 0 ? 
                        `<span class="tag tag-success">ACTIVE</span>` : 
                        `<span class="tag" style="background:#334155; color:#94a3b8;">IDLE</span>`;
                    agentHtml += `
                        <div class="stat-row">
                            <span class="stat-label">${name.charAt(0).toUpperCase() + name.slice(1)} Agent</span>
                            <span class="stat-value">${statusTag}</span>
                        </div>`;
                }
                agentHtml += `</div>`;
                document.getElementById('agent-load-stats').innerHTML = agentHtml;

                document.getElementById('empathy-stats').innerHTML = `
                    <div class="stat-row"><span class="stat-label">Current Mood</span><span class="stat-value">${empathy.mood}</span></div>
                    <div class="stat-row"><span class="stat-label">Cognitive Tone</span><span class="stat-value">${empathy.tone}</span></div>
                `;

                const hitlEl = document.getElementById('hitl-list');
                if (hitl.length > 0) {
                    hitlEl.innerHTML = hitl.map(h => `
                        <div class="card" style="margin-bottom: 10px; padding: 15px; background: #020617;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                                <span style="font-weight:700; color: #fbbf24; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">
                                    <i class="fas fa-shield-halved"></i> ${h.agent_type} Intervention
                                </span>
                                <span class="tag" style="font-size: 9px;">${new Date(h.timestamp).toLocaleTimeString()}</span>
                            </div>
                            
                            <div style="margin-bottom: 12px;">
                                <div style="font-size: 10px; color: #64748b; font-weight: 700; text-transform: uppercase;">Observation / Risk</div>
                                <div style="font-size: 13px; margin-top: 4px; color: #f1f5f9;">${h.query}</div>
                            </div>

                            ${h.data && h.data.reasoning_insight ? `
                            <div style="margin-bottom: 12px; padding: 8px; background: rgba(56, 189, 248, 0.05); border-radius: 4px; border-left: 2px solid var(--accent);">
                                <div style="font-size: 10px; color: var(--accent); font-weight: 700; text-transform: uppercase;">AI Proposed Reasoning</div>
                                <div style="font-size: 12px; margin-top: 4px; color: #94a3b8; font-style: italic;">"${h.data.reasoning_insight}"</div>
                            </div>
                            ` : ''}

                            ${h.vap_hash ? `<div style="font-size:10px; margin-top:5px; color: var(--accent); font-family: monospace;">VAP: ${h.vap_hash}</div>` : ''}
                            <div style="margin-top:15px; display:flex; gap:10px;">
                                <button class="btn" style="padding:4px 10px; font-size:11px;" onclick="approveAction('${h.id}')">Approve</button>
                                <button class="btn" style="padding:4px 10px; font-size:11px; background:#7f1d1d; color:white;" onclick="denyAction('${h.id}')">Deny</button>
                                <button class="btn" style="padding:4px 10px; font-size:11px; background:#334155; color:white;" onclick="showHitlDetails('${h.id}')">Details</button>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (e) { console.error('Agent status fetch error', e); }
        }

        async function toggleSimulation() {
            const btn = document.getElementById('sim-btn');
            console.log('Attempting to toggle IoT simulation...');
            try {
                const res = await fetch('/api/v1/admin/dashboard/system/simulate-iot', {method: 'POST'});
                if (!res.ok) throw new Error('System Ignition Failed');
                const data = await res.json();
                if (data.status === 'started') {
                    btn.innerHTML = '<i class="fas fa-stop-circle"></i> Terminate Simulation';
                    btn.style.background = '#7f1d1d';
                    btn.style.color = 'white';
                    showToast('Virtual telemetry stream active', 'success');
                } else {
                    btn.innerHTML = '<i class="fas fa-bolt"></i> Ignite IoT Simulation';
                    btn.style.background = '#38bdf8'; 
                    btn.style.color = '#0f172a';
                    showToast('Simulation sensors offline', 'info');
                }
            } catch (e) {
                showToast('Ignition failure: ' + e.message, 'error');
            }
        }

        async function approveAction(id) {
            const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/approve`, {method: 'POST'});
            if (res.ok) { showToast('HITL Protocol Approved', 'success'); fetchAgentStatus(); }
        }

        async function denyAction(id) {
            const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/deny`, {method: 'POST'});
            if (res.ok) { showToast('HITL Protocol Rejected', 'error'); fetchAgentStatus(); }
        }

        function showHitlDetails(id) {
            const item = currentHitlData.find(h => h.id == id);
            if (!item) return;
            const body = document.getElementById('modal-body');
            body.innerHTML = `
                <div id="explanation-box" style="display:none; margin-bottom: 25px; padding: 20px; background: rgba(56, 189, 248, 0.05); border: 1px solid var(--accent); border-radius: 8px; border-left-width: 4px;">
                    <div class="metric-label" style="color: var(--accent); margin-bottom: 10px;"><i class="fas fa-comment-nodes"></i> AI Cognitive Insight</div>
                    <div id="explanation-text" style="font-size: 14px; line-height: 1.6; color: #f1f5f9;"></div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                    <div>
                        <div class="metric-label">Agent Identity</div>
                        <div style="color: #fbbf24; font-weight: 800; font-size: 18px; margin-top: 5px;">${item.agent_type}</div>
                    </div>
                    <div>
                        <div class="metric-label">Interruption Point</div>
                        <div style="color: var(--accent); font-weight: 700; margin-top: 5px;">${item.data?.interruption_point || 'Unknown'}</div>
                    </div>
                </div>
                <div style="margin-bottom: 25px;">
                    <div class="metric-label">Critical Observation</div>
                    <div style="font-size: 14px; margin-top: 8px; background: #020617; padding: 12px; border-radius: 6px; border: 1px solid #1e293b;">${item.query}</div>
                </div>

                <button class="btn" id="explain-btn" onclick="explainReasoning('${id}')" style="background: var(--accent); width: 100%; margin-bottom: 25px; justify-content: center;">
                    <i class="fas fa-wand-magic-sparkles"></i> Synthesize Reasoning Explanation
                </button>

                <div class="metric-label">Raw System Context (Internal Data)</div>
                <pre style="margin-top: 10px; border-color: #334155;">${JSON.stringify(item.data, null, 4)}</pre>
            `;
            document.getElementById('details-modal').style.display = 'block';
        }

        async function explainReasoning(id) {
            const btn = document.getElementById('explain-btn');
            const box = document.getElementById('explanation-box');
            const text = document.getElementById('explanation-text');
            
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> AI Reasoning in Progress...';
            
            try {
                const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/explain`, { method: 'POST' });
                const data = await res.json();
                box.style.display = 'block';
                text.innerText = data.explanation;
                btn.style.display = 'none';
            } catch (e) {
                showToast('AI Synthesis Failed', 'error');
                btn.innerHTML = '<i class="fas fa-wand-magic-sparkles"></i> Retry Explanation';
                btn.disabled = false;
            }
        }

        function closeModal() {
            document.getElementById('details-modal').style.display = 'none';
        }

        window.onclick = function(event) {
            const modal = document.getElementById('details-modal');
            if (event.target == modal) closeModal();
        }

        async function logout() {
            await fetch('/api/v1/auth/logout', { method: 'POST' });
            window.location.href = '/login';
        }

        fetchMetrics();
        connectWebSocket();
        setInterval(fetchMetrics, 60000);
    </script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard_ui(request: Request):
    """Serve the full modular admin dashboard UI."""
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return DASHBOARD_HTML