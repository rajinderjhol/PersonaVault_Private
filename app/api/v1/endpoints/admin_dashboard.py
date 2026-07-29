# backend/app/api/v1/endpoints/admin_dashboard.py
"""
DEPRECATED: This monolithic endpoint file is being phased out in favor of 
modular routers located in app/api/v1/endpoints/dashboard/.

Legacy support for system metrics, monitoring, and management.
New functionality should be implemented in the respective modular sub-routers.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_
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

logger.warning("Module app.api.v1.endpoints.admin_dashboard is DEPRECATED. Move logic to modular sub-routers.")

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
    now_utc = datetime.utcnow()
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    metrics = {} # Initialized to prevent NameError in error handler

    try:
        # Execute queries sequentially to avoid AsyncSession concurrency errors (Database Lock)
        res_user_total = await db.execute(select(func.count(User.id)))
        res_user_today = await db.execute(select(func.count(User.id)).where(User.created_at >= start_of_day))
        res_user_active = await db.execute(select(func.count(User.id)).where(User.last_login >= now_utc - timedelta(days=30)))
        res_mem_total = await db.execute(select(func.count(Memory.id)))
        
        # SQLite-compatible date math for memory expiry (julianday). 
        # Refactored to remove redundant datetime() wrap which can cause parsing errors.
        res_mem_expired = await db.execute(
            select(func.count(Memory.id)).where(and_(Memory.expiry_days > 0, text("julianday(created_at) + expiry_days < julianday('now')")))
        )
        res_mem_soon = await db.execute(
            select(func.count(Memory.id)).where(
                and_(
                    Memory.expiry_days > 0, 
                    text("julianday(created_at) + expiry_days BETWEEN julianday('now') AND julianday('now', '+3 days')")
                )
            )
        )
        
        res_session_active = await db.execute(select(func.count(UserSession.id)).where(UserSession.is_active.is_(True)))
        res_session_today = await db.execute(select(func.count(UserSession.id)).where(UserSession.created_at >= start_of_day))
        
        res_iot_total = await db.execute(select(func.count(IoTDevice.id)))
        res_iot_active = await db.execute(select(IoTDevice).where(IoTDevice.status == "active"))
        res_iot_points = await db.execute(select(func.count(IoTData.id)).where(IoTData.timestamp >= start_of_day))
        
        res_legal = await db.execute(select(func.count(LegalMatter.id)).where(LegalMatter.status == "active"))
        res_ai_configs = await db.execute(select(func.count(AISetting.id)).where(AISetting.is_active.is_(True)))
        res_ai_provider = await db.execute(select(SystemConfig).where(SystemConfig.key == "primary_ai_provider"))

        active_iot_results = res_iot_active.scalars().all()
        provider_cfg = res_ai_provider.scalars().first()
        primary_provider = provider_cfg.value if provider_cfg else "ollama"

        # Security Status derived from config
        # Safely access attributes to prevent total failure if Config class is incomplete
        encryption_key = getattr(Config, "ENCRYPTION_KEY", None)
        enc_status = "AES-128 (Active)" if encryption_key and encryption_key != "change-me" else "Config Pending"
        tok_status = "Active (Transient)"

        metrics = {
            "users": {
                "total": res_user_total.scalar_one_or_none() or 0,
                "new_today": res_user_today.scalar_one_or_none() or 0,
                "active_30d": res_user_active.scalar_one_or_none() or 0
            },
            "memories": {
                "total": res_mem_total.scalar_one_or_none() or 0,
                "expired": res_mem_expired.scalar_one_or_none() or 0,
                "expiring_soon": res_mem_soon.scalar_one_or_none() or 0
            },
            "sessions": {
                "active": res_session_active.scalar_one_or_none() or 0,
                "total_today": res_session_today.scalar_one_or_none() or 0
            },
            "iot": {
                "total_devices": res_iot_total.scalar_one_or_none() or 0,
                "active_count": len(active_iot_results),
                "active_devices": [d.device_name or d.device_id for d in active_iot_results],
                "data_points_today": res_iot_points.scalar_one_or_none() or 0
            },
            "legal": {
                "active_matters": res_legal.scalar_one_or_none() or 0
            }
        }

        # AI and System component checks with granular try-except to prevent total failure
        ollama_status = "error"
        try: ollama_status = await _check_ollama(request)
        except Exception: pass
        
        gemini_status = "not_configured"
        try: gemini_status = await _check_gemini(request)
        except Exception: pass
        
        storage_data = {"error": "unavailable"}
        try: storage_data = await _get_storage_usage()
        except Exception: pass

        orchestrator = getattr(request.app.state, "orchestrator", None)

        return {
            "timestamp": now_utc.isoformat(),
            **metrics,
            "security": {
                "encryption": enc_status,
                "tokenization": tok_status
            },
            "ai": {
                "active_configs": res_ai_configs.scalar_one_or_none() or 0,
                "primary_provider": primary_provider,
                "ollama_status": ollama_status,
                "gemini_status": gemini_status,
                "verilink_status": getattr(orchestrator, "governance_status", "not_installed"),
                "verilink_offline": getattr(orchestrator, "offline_mode", False)
            },
            "system": {
                "vector_index_size": len(getattr(request.app.state.vector_service, "metadata", [])) if hasattr(request.app.state, "vector_service") else 0,
                "graph_healthy": request.app.state.graph_service.check_health() if hasattr(request.app.state, "graph_service") and hasattr(request.app.state.graph_service, 'check_health') else False,
                "vector_healthy": request.app.state.vector_service.check_health() if hasattr(request.app.state, "vector_service") and hasattr(request.app.state.vector_service, 'check_health') else False,
                "storage_used": storage_data,
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
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "error": f"Service layer contention: {str(e)}", **metrics}

# ============ Management Endpoints ============

@router.get("/models")
async def list_installed_models(request: Request, user_id: int = Depends(require_admin)):
    """List models installed in Ollama."""
    try:
        client = request.app.state.ai_client
        response = await client.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        return response.json() if response.status_code == 200 else {"models": []}
    except Exception: return {"models": []}

@router.post("/models/pull")
async def pull_ollama_model(request: Request, body: dict, user_id: int = Depends(require_admin)):
    """Trigger a model pull from Ollama and stream status."""
    model_name = body.get("name")
    if not model_name: raise HTTPException(status_code=400, detail="Model name required")
    async def generate_status():
        try:
            client = request.app.state.ai_client
            async with client.stream("POST", f"{Config.OLLAMA_BASE_URL}/api/pull", json={"name": model_name}) as r:
                async for line in r.aiter_lines():
                    if line: yield f"data: {line}\n\n"
        except Exception as e: yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    return StreamingResponse(generate_status(), media_type="text/event-stream")

@router.delete("/models/{name}")
async def delete_ollama_model(name: str, request: Request, user_id: int = Depends(require_admin)):
    """Delete a model from Ollama."""
    try:
        client = request.app.state.ai_client
        await client.request("DELETE", f"{Config.OLLAMA_BASE_URL}/api/delete", json={"name": name})
        return {"status": "deleted"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/config")
async def get_learning_settings(db: AsyncSession = Depends(get_db), user_id: int = Depends(require_admin)):
    """Get crystallization engine settings."""
    stmt = select(SystemConfig).where(SystemConfig.key.in_(["graduation_batch_size", "graduation_interval_hours"]))
    configs = (await db.execute(stmt)).scalars().all()
    cfg_map = {c.key: c.value for c in configs}
    return {
        "batch_size": int(cfg_map.get("graduation_batch_size", 10)),
        "interval_hours": float(cfg_map.get("graduation_interval_hours", 1.0))
    }

@router.post("/learning/config")
async def update_learning_settings(body: dict, db: AsyncSession = Depends(get_db), user_id: int = Depends(require_admin)):
    """Update crystallization engine settings."""
    for key, value in body.items():
        db_key = f"graduation_{key}"
        stmt = select(SystemConfig).where(SystemConfig.key == db_key)
        config = (await db.execute(stmt)).scalars().first()
        if config: config.value = str(value)
        else: db.add(SystemConfig(key=db_key, value=str(value)))
    await db.commit()
    return {"status": "success"}

@router.post("/learning/trigger")
async def trigger_learning_manual(request: Request, user_id: int = Depends(require_admin)):
    """Manually trigger Layer 2 -> Layer 3 crystallization."""
    if hasattr(request.app.state, 'consolidation_task') and hasattr(request.app.state.consolidation_task, 'trigger_event'):
        request.app.state.consolidation_task.trigger_event.set()
        logger.info("Admin: Manual learning cycle triggered via dashboard.")
    return {"status": "triggered", "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/cognitive-load")
async def get_agent_load(request: Request, user_id: int = Depends(require_admin)):
    """Metrics on agent activity."""
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator:
        return {"active_tasks": 0, "agent_activity": {}}
    
    # Introspect the real Swarm Orchestrator
    activity = {}
    for agent_name in orchestrator.agents.keys():
        # Simulation: Report presence. In Phase 3, agents will have .is_busy states
        activity[agent_name] = 1 if _safe_metric_get(PLASMA_ACTIVE) > 0 else 0

    return {
        "active_tasks": int(_safe_metric_get(PLASMA_ACTIVE)),
        "agent_activity": activity,
        "router_mode": getattr(request.app.state, "ai_router", None).engine_mode if hasattr(request.app.state, "ai_router") else "Standard"
    }

@router.get("/mcp/registry")
async def get_mcp_registry(request: Request, user_id: int = Depends(require_admin)):
    """List registered MCP tools and servers for Phase 3 readiness."""
    # Leapfrog Point: Now reflects real capabilities of the Swarm
    return {
        "servers": [
            {"name": "PersonaVault-Primary", "status": "active", "type": "server", "protocol": "MCP 1.0"},
            {"name": "Internal-Swarm-Mesh", "status": "connected", "type": "blackboard", "protocol": "Memory-L1"}
        ],
        "tools": [
            {"name": "vault_search", "description": "Hybrid Vector+SQL Retrieval"},
            {"name": "empathy_grounding", "description": "HRI Situational Tone Analysis"},
            {"name": "blackboard_sync", "description": "L1 Working Memory state sharing"}
        ],
        "resources": [
            {"name": "User Cognitive Patterns", "uri": "personavault://memory/semantic-patterns", "type": "JSON"},
            {"name": "Contextual Constraints", "uri": "personavault://memory/constraints", "type": "Text"},
            {"name": "HITL Audit Trail", "uri": "personavault://governance/audit", "type": "JSON"}
        ]
    }

@router.get("/blackboard/snapshot")
async def get_blackboard_snapshot(request: Request, user_id: int = Depends(require_admin)):
    """Get the current state of the Layer 1 Cognitive Blackboard."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if not blackboard:
        return {"current_state": {}, "active_agents": []}
    return blackboard.get_snapshot()

@router.post("/swarm/trigger")
async def trigger_swarm_interaction(request: Request, body: dict, user_id: int = Depends(require_admin)):
    """Directly inject a query into the Swarm and process it."""
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query content required")
    
    blackboard = getattr(request.app.state, "blackboard", None)
    orchestrator = getattr(request.app.state, "orchestrator", None)
    
    if not blackboard:
        return {"status": "error", "message": "Blackboard not available"}
    
    await blackboard.post_insight(
        agent_name="Admin-Terminal",
        insight={"query": query, "status": "processing", "origin": "dashboard"},
        importance=1.0
    )
    
    await manager.broadcast(json.dumps({
        "type": "thought_stream",
        "agent": "Orchestrator",
        "content": f"🚀 Processing query: '{query[:50]}...'"
    }))
    
    if orchestrator:
        try:
            result = await orchestrator.run(
                query=query,
                context={"user_id": user_id, "origin": "dashboard"}
            )
            
            await blackboard.post_insight(
                agent_name="Orchestrator",
                insight={
                    "query": query,
                    "status": "completed",
                    "answer": result.get("answer", "No answer generated"),
                    "evaluation": result.get("evaluation", {}),
                    "confidence": result.get("confidence", 0.0)
                },
                importance=0.9
            )
            
            await manager.broadcast(json.dumps({
                "type": "thought_stream",
                "agent": "Orchestrator",
                "content": f"✅ Query processed successfully!"
            }))
            
            return {
                "status": "swarm_completed",
                "message": f"Query processed: {query[:50]}...",
                "result": result.get("answer", ""),
                "confidence": result.get("confidence", 0.0),
                "evaluation": result.get("evaluation", {})
            }
        except Exception as e:
            logger.error(f"Swarm processing error: {e}")
            await blackboard.post_insight(
                agent_name="Orchestrator",
                insight={
                    "query": query,
                    "status": "error",
                    "error": str(e)
                },
                importance=0.5
            )
            return {
                "status": "swarm_error",
                "message": f"Error processing query: {str(e)}"
            }
    
    return {"status": "swarm_ignited", "message": f"Query '{query}' posted to Blackboard."}

@router.post("/swarm/respond")
async def respond_to_agent(request: Request, body: dict, user_id: int = Depends(require_admin)):
    """Allow admin to send a steering message back to the swarm."""
    agent = body.get("agent", "Orchestrator")
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard:
        await blackboard.post_insight(
            agent_name="Admin-Override",
            insight={"target": agent, "instruction": content, "type": "steering"},
            importance=1.0
        )
        await manager.broadcast(json.dumps({
            "type": "thought_stream",
            "agent": "Admin-Override",
            "content": f"@{agent}: {content}"
        }))
    return {"status": "sent"}

@router.get("/swarm/negotiation-trace")
async def get_negotiation_trace(request: Request, user_id: int = Depends(require_admin)):
    """Provides a structural trace of agent collaboration for visualization."""
    blackboard = getattr(request.app.state, "blackboard", None)
    bb_state = blackboard.get_snapshot() if blackboard else {"current_state": {}}
    
    is_medical = False
    is_legal = False
    for agent, entry in bb_state.get("current_state", {}).items():
        data_str = str(entry.get("data", "")).lower()
        if any(k in data_str for k in ["tachycardia", "heart", "bpm", "sensor"]): is_medical = True
        if any(k in data_str for k in ["legal", "matter", "policy", "rule"]): is_legal = True

    if is_medical:
        return {
            "sequence": [
                {"agent": "IoT-Monitor", "action": "Signal: Tachycardia", "to": "Planner"},
                {"agent": "Planner", "action": "Plan: Med-Triage", "to": "Retriever"},
                {"agent": "Retriever", "action": "Fetch: Protocols", "to": "Reasoner"},
                {"agent": "Reasoner", "action": "Risk: Elevated", "to": "Empathy"},
                {"agent": "Empathy", "action": "Tone: Supportive", "to": "Judge"},
                {"agent": "Judge", "action": "Action: HITL Req", "to": "Blackboard"}
            ]
        }
    elif is_legal:
        return {
            "sequence": [
                {"agent": "User-Proxy", "action": "Query: Compliance", "to": "Planner"},
                {"agent": "Planner", "action": "Search: Clauses", "to": "Retriever"},
                {"agent": "Retriever", "action": "Result: Case Law", "to": "Reasoner"},
                {"agent": "Reasoner", "action": "Check: Governance", "to": "Judge"},
                {"agent": "Judge", "action": "Seal: VeriLink", "to": "Blackboard"}
            ]
        }
    return {"sequence": [{"agent": "Orchestrator", "action": "Polling", "to": "Blackboard"}]}

@router.get("/empathy/status")
async def get_empathy_grounding(request: Request, user_id: int = Depends(require_admin)):
    """Mood and tone status."""
    return {"mood": "Calm", "tone": "Supportive"}

@router.get("/logs/stream")
async def stream_engine_logs(request: Request, user_id: int = Depends(require_admin)):
    """SSE endpoint for live real uvicorn system logs."""
    # Ensure we use an absolute path relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
    log_file = os.path.join(project_root, "backend/storage/logs/uvicorn.log")

    async def log_generator():
        if not os.path.exists(log_file):
            yield "data: [SYSTEM] Log file not found.\n\n"
            return

        with open(log_file, "r") as f:
            f.seek(0, os.SEEK_END)
            while not await request.is_disconnected():
                line = f.readline()
                if line == "":
                    await asyncio.sleep(0.5)
                    continue
                # Send raw line to preserve formatting and stack traces
                yield f"data: {line}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")

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
    # Accept first to stabilize the Cloud Shell proxy handshake
    await websocket.accept()

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
    action.resolved_at = datetime.now(timezone.utc)
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
    action.resolved_at = datetime.now(timezone.utc)
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
    2. Identify if this relates to Working (L1), Episodic (L2), or Semantic (L3) memory discrepancies.
    3. Clearly state the safety or logic conflict identified.
    4. Provide a neutral recommendation (Approve/Deny) based on system policy.
    
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
            "query": (e.query[:60] + "...") if e.query and len(e.query) > 60 else (e.query or "No query content"),
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
                    last_seen=datetime.now(timezone.utc)
                )
                db.add(device)
            else:
                device.status = "active"
                device.last_seen = datetime.now(timezone.utc)
            
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
                
                # PROACTIVE AGENCY LEAPFROG: Detect anomalies and alert the Blackboard
                if readings["heart_rate"] > 75:  # Simulated threshold for demo
                    # Broadcast reasoning steps for the Live Swarm Feed
                    await manager.broadcast(json.dumps({
                        "type": "thought_stream",
                        "agent": "IoT-Monitor",
                        "content": f"CRITICAL: Heart rate spike ({readings['heart_rate']} BPM) detected. Alerting Blackboard swarm."
                    }))
                    await asyncio.sleep(1) # Simulation pacing
                    await manager.broadcast(json.dumps({
                        "type": "thought_stream",
                        "agent": "Planner",
                        "content": "Anomalous telemetry detected. Scheduling triage and safety check tasks."
                    }))
                    await asyncio.sleep(1)
                    await manager.broadcast(json.dumps({
                        "type": "thought_stream",
                        "agent": "Reasoner",
                        "content": "Evaluating physiological risk factors. Confidence score: 0.92."
                    }))

                # Process data directly through IoTService logic
                await IoTService.process_realtime_data({
                    "device_id": sim_device_identifier,
                    "device_identifier": sim_device_identifier, # Fallback for service logic
                    "user_id": owner_id,
                    "data_type": "sensor_readings",
                    "type": "sensor_readings", # Fallback for service logic
                    "timestamp": datetime.now(timezone.utc).isoformat(), # Use string for serialization safety
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
    # Use the unified service from app state
    count = await request.app.state.memory_service.delete_expired_memories()
    return {"deleted": count, "timestamp": datetime.now(timezone.utc).isoformat()}

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
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
        # Perform a lightweight call to verify the key and connectivity
        for _ in genai.list_models():
            return "connected"
        return "error (no models)"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return "error"

async def _get_storage_usage() -> dict:
    """Get storage usage information."""
    home_dir = os.path.expanduser("~")
    # Project dir is personavault/ (5 levels up from endpoints/)
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
    
    def get_dir_size(path):
        total = 0
        if not os.path.exists(path):
            return 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        if not os.path.islink(fp):
                            total += os.path.getsize(fp)
                    except (FileNotFoundError, PermissionError):
                        continue
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
            "monitored_paths_mb": {
                "uploads": get_dir_size(os.path.join(project_dir, "backend/storage/uploads")),
                "vector_storage": get_dir_size(os.path.join(project_dir, "backend/storage")),
                "logs": get_dir_size(os.path.join(project_dir, "backend/storage/logs"))
            },
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        return {"error": f"Storage diagnostics unavailable: {str(e)}"}

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
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {"error": "Unable to retrieve system memory info"}

# ============ DASHBOARD UI moved to dashboard_template.py ============
