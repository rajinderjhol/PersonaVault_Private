"""
Modular Dashboard Router - Serves individual tab content
"""
from fastapi import APIRouter, Depends, Request, status, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_
from datetime import datetime, timedelta, timezone
print("!!! DASHBOARD ROUTER LOADED !!!")
import os
import time
import logging
import json
import psutil
import shutil
import random
import asyncio

from app.core.dependencies import require_admin
from app.api.v1.endpoints.auth import get_current_user_logic as get_current_user
from app.db.session import get_db, SessionLocal
from app.models import (
    User, Memory, AuditLog, UserSession, SystemConfig,
    AISetting, IoTDevice, IoTData, LegalMatter, PendingAction, EpisodicEntry
)
from app.config import Config
from app.utils.websocket import manager
from app.services.iot_service import IoTService
from app.services.custom import (
    CRYSTALLIZATION_VELOCITY, SUBLIMATION_COUNT, PLASMA_ACTIVE, AGENT_STATUS,
    EVAPORATION_COUNT, CONDENSATION_VELOCITY
)
from app.models import User, IoTDevice, IoTData, SystemConfig
from app.services.intelligence_gateway import gateway
from app.services.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)
from app.api.v1.endpoints.dashboard.routers.model_router import router as model_router
from app.api.v1.endpoints.dashboard.routers.metrics_router import router as metrics_router
from app.api.v1.endpoints.dashboard.routers.governance_router import router as governance_router
from app.api.v1.endpoints.dashboard.routers.config_router import router as config_router
from app.api.v1.endpoints.dashboard.routers.maintenance_router import router as maintenance_router
from app.api.v1.endpoints.dashboard.routers.learning_router import router as learning_router
from app.api.v1.endpoints.dashboard.routers.blackboard_router import router as blackboard_router
from app.api.v1.endpoints.dashboard.routers.swarm_router import router as swarm_router

router = APIRouter(tags=["admin"])
router.include_router(model_router)
router.include_router(metrics_router)
router.include_router(governance_router)
router.include_router(config_router)
router.include_router(maintenance_router)
router.include_router(learning_router)
router.include_router(blackboard_router)
router.include_router(swarm_router)
TEMPLATE_DIR = Path(__file__).parent / "templates"
# Fallback for tab lookups to search main templates if not in v2
TAB_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _safe_metric_get(metric, default=0, labels=None):
    try:
        if labels:
            return metric.labels(**labels)._value.get()
        if hasattr(metric, '_value') and hasattr(metric._value, 'get'):
            return metric._value.get()
        if hasattr(metric, 'value'):
            return metric.value
        return float(metric) if metric is not None else default
    except:
        return default


@router.get("/", response_class=HTMLResponse)
async def dashboard_ui(request: Request, db: AsyncSession = Depends(get_db)):
    """Serve the main dashboard UI with modular tabs (Legacy)."""
    try:
        # Check authentication manually
        await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        raise e
    
    base_path = TEMPLATE_DIR / "base.html"
        
    if not base_path.exists():
        logger.error(f"Dashboard base template not found: {base_path}")
        return HTMLResponse("<h1>Dashboard template not found</h1>", status_code=404)
        
    logger.info(f"Loading legacy dashboard template from: {base_path}")
    try:
        with open(base_path, "r") as f:
            return HTMLResponse(f.read())
    except Exception as e:
        logger.error(f"Error reading dashboard template: {e}")
        return HTMLResponse("<h1>Error loading dashboard</h1>", status_code=500)


@router.get("/v2", response_class=HTMLResponse)
async def dashboard_v2_ui(request: Request, db: AsyncSession = Depends(get_db)):
    """Serve v2 (three-panel) dashboard UI."""
    try:
        await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        raise e
    
    base_path = TEMPLATE_DIR / "v2" / "base.html"
        
    if not base_path.exists():
        logger.error(f"V2 Dashboard base template not found: {base_path}")
        return HTMLResponse("<h1>V2 Dashboard template not found</h1>", status_code=404)
        
    logger.info(f"Loading v2 dashboard template from: {base_path}")
    try:
        with open(base_path, "r") as f:
            return HTMLResponse(f.read())
    except Exception as e:
        logger.error(f"Error reading v2 dashboard template: {e}")
        return HTMLResponse("<h1>Error loading v2 dashboard</h1>", status_code=500)


@router.get("/intelligence-sources", response_class=HTMLResponse)
async def intelligence_sources_ui(request: Request, db: AsyncSession = Depends(get_db)):
    """Serve Intelligence Source Control dashboard UI."""
    try:
        await get_current_user(request, db)
    except HTTPException as e:
        if e.status_code == 401:
            return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        raise e
    
    template_path = TAB_TEMPLATE_DIR / "v2" / "intelligence_source_control.html"
    if not template_path.exists():
        return HTMLResponse("<h1>Template not found</h1>", status_code=404)
    
    with open(template_path, "r") as f:
        return HTMLResponse(f.read())





@router.post("/swarm/trigger")
async def trigger_swarm_interaction(request: Request, body: dict, user_id: int = Depends(require_admin)):
    """Directly inject a query into the Swarm and process it."""
    query = body.get("query", "")
    session_id = body.get("session_id")
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
                context={"user_id": user_id, "origin": "dashboard", "session_id": session_id}
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


@router.get("/swarm/negotiation-trace")
async def get_negotiation_trace(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Get the real swarm negotiation trace from blackboard history."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard and blackboard.history:
        history = blackboard.history[-10:]
        sequence = []
        for i in range(len(history)):
            step = history[i]
            target = history[i+1].get("agent", "Blackboard") if i < len(history) - 1 else "Blackboard"
            sequence.append({
                "agent": step.get("agent", "Unknown"),
                "to": target,
                "action": step.get("data", {}).get("event", "insight")
            })
        return {"sequence": sequence}
    return {"sequence": []}




@router.get("/mcp/registry")
async def get_mcp_registry(request: Request, user_id: int = Depends(require_admin)):
    return {
        "servers": [{"name": "PersonaVault-Primary", "status": "active", "protocol": "MCP 1.0"}],
        "tools": [
            {"name": "vault_search", "description": "Hybrid Vector+SQL Retrieval"},
            {"name": "empathy_grounding", "description": "HRI Situational Tone Analysis"},
            {"name": "blackboard_post", "description": "Inject an insight into the cognitive mesh"}
        ]
    }


# ============ CHAT AND HISTORY ============

@router.get("/chat/history")
async def get_chat_history(user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Retrieve recent chat history from episodic memory logs."""
    stmt = select(Memory).where(Memory.tags.like("%interaction_log%")).order_by(Memory.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [{"content": l.content, "timestamp": l.created_at.isoformat()} for l in reversed(logs)]


@router.get("/chat")
async def get_chat_with_version():
    """Serve chat.html with version for cache busting."""
    version = "1.0.1"
    try:
        with open("app/version.txt", "r") as f:
            version = f.read().strip()
    except:
        pass
    
    html_path = Path(__file__).parent / "templates" / "chat.html"
    if html_path.exists():
        with open(html_path, "r") as f:
            content = f.read()
        return HTMLResponse(content)
    return HTMLResponse("<h1>Chat not found</h1>", status_code=404)




# ============ BLACKBOARD ============

@router.get("/blackboard/snapshot")
async def get_blackboard_snapshot(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Get the current blackboard state (cognitive shared memory)."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard:
        snapshot = blackboard.get_snapshot()
        return {
            "current_state": snapshot.get("current_state", {}),
            "active_agents": snapshot.get("active_agents", []),
            "conflict_history": snapshot.get("conflict_history", [])
        }
    return {"current_state": {}, "active_agents": [], "conflict_history": []}







# ============ TABS ============

@router.get("/tab/{tab_id}", response_class=HTMLResponse)
async def get_tab(tab_id: str, user_id: int = Depends(require_admin)):
    """Serve individual tab content."""
    # Map complex tab IDs to simplified filenames if necessary
    mapping = {
        "domain-security": "security",
        "domain-compliance": "governance",
        "domain-swarm": "swarm"
    }
    safe_tab_id = mapping.get(tab_id, tab_id)
    
    # Check if this is a V2 tab
    tab_path = TAB_TEMPLATE_DIR / f"{safe_tab_id}.html"
    if not tab_path.exists():
        tab_path = TAB_TEMPLATE_DIR / "v2" / f"{safe_tab_id}.html"

    if tab_path.exists():
        with open(tab_path, "r") as f:
            return HTMLResponse(f.read())

    # Fallbacks (for robust UI)
    fallbacks = {
        "overview": '<div id="metrics-grid" class="grid"></div><div class="card"><h3 class="card-title">Intelligence Feed</h3><pre id="raw-metrics">Initializing system state...</pre></div>',
        "models": '<div class="card"><h3 class="card-title">Ollama Node</h3><div id="models-list" style="display:flex; flex-direction:column; gap:12px;"></div></div>',
        "logs": '<div class="card" style="height:500px; display:flex; flex-direction:column;"><div id="log-container" class="log-container"></div></div>',
        "agents": '<div class="grid"><div class="card"><div class="card-title">Cognitive Load</div><div id="agent-load-stats" class="mt-10"></div></div><div class="card"><div class="card-title">Empathy & Tone</div><div id="empathy-stats" class="mt-10"></div></div></div><div class="card"><div class="card-title">Human-In-The-Loop</div><div id="hitl-list" class="mt-10"></div></div>',
        "mcp": '<div class="grid"><div class="card"><div class="card-title">Registered Nodes</div><div id="mcp-servers-list" class="mt-10"></div></div><div class="card"><div class="card-title">Available Swarm Tools</div><div id="mcp-tools-list" class="mt-10"></div></div></div>',
        "lattices": '<div class="card" style="margin-bottom: 25px; border-left: 4px solid #a855f7;"><div class="metric-label">Memory Distribution Ratio</div><div class="mem-viz-container"><div id="bar-l2" class="viz-l2" style="width: 10%"></div><div id="bar-l3" class="viz-l3" style="width: 10%"></div></div></div><div class="grid"><div class="card"><div class="metric-label">Layer 1 (Gas)</div><div class="metric-value">Active</div></div><div class="card"><div class="metric-label">Layer 2 (Liquid)</div><div id="layer2-count" class="metric-value">0</div></div><div class="card"><div class="metric-label">Layer 3 (Ice)</div><div id="layer3-count" class="metric-value">0</div></div></div>',
        "learning_dashboard": '<div id="learning-dashboard-tab" class="card"><h3 class="card-title">📊 Learning Dashboard</h3><div id="pattern-feed">Loading patterns...</div></div>',
        "evidence": '<div class="card"><h3 class="card-title">Evidence Pipeline</h3><div id="evidence-stats-container">Loading...</div></div>'
    }
    return HTMLResponse(fallbacks.get(tab_id, f"<div class='metric-label'>Fragment '{tab_id}' not found</div>"))


@router.get("/tab/decision-intelligence")

async def get_decision_intelligence_tab():
    """Return the decision intelligence dashboard tab HTML."""
    html_path = TEMPLATE_DIR / "decision_intelligence.html"
    if html_path.exists():
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h2 style=\"color: var(--accent);\">🎯 Decision Intelligence</h2><div class=\"card\"><p style=\"color: #94a3b8;\">Loading...</p></div>")


@router.get("/decision/intelligence/stats")
async def get_decision_intelligence_stats(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get decision intelligence stats for the dashboard."""
    from app.models import BehaviourEvent, SemanticPattern
    from sqlalchemy import select, func, desc
    
    total_stmt = select(func.count(BehaviourEvent.id))
    total_result = await db.execute(total_stmt)
    total_decisions = total_result.scalar_one() or 0
    
    success_stmt = select(func.count(BehaviourEvent.id)).where(BehaviourEvent.outcome == "success")
    success_result = await db.execute(success_stmt)
    success_count = success_result.scalar_one() or 0
    success_rate = (success_count / total_decisions * 100) if total_decisions > 0 else 0
    
    avg_stmt = select(func.avg(BehaviourEvent.confidence))
    avg_result = await db.execute(avg_stmt)
    avg_confidence = avg_result.scalar_one() or 0
    
    patterns_stmt = select(func.count(SemanticPattern.id))
    patterns_result = await db.execute(patterns_stmt)
    patterns_learned = patterns_result.scalar_one() or 0
    
    recent_stmt = select(BehaviourEvent).order_by(desc(BehaviourEvent.timestamp)).limit(10)
    recent_result = await db.execute(recent_stmt)
    recent_decisions = recent_result.scalars().all()
    
    confidence_history = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.78, 0.82, 0.85]
    
    return {
        "total_decisions": total_decisions,
        "success_rate": round(success_rate, 1),
        "avg_confidence": round(avg_confidence * 100, 1),
        "patterns_learned": patterns_learned,
        "decisions": [
            {
                "type": d.event_type,
                "query": d.reason[:100] + ("..." if len(d.reason) > 100 else ""),
                "confidence": d.confidence,
                "outcome": d.outcome,
                "timestamp": d.timestamp.isoformat()
            }
            for d in recent_decisions
        ],
        "confidence_history": confidence_history
    }


from app.api.v1.endpoints.dashboard.utils import (
    _safe_metric_get, _check_ollama, _check_gemini, _get_storage_usage, 
    _get_cpu_usage, _get_memory_usage
)


async def _run_iot_simulation():
    """Background task to simulate IoT data flow."""
    sim_device_identifier = "simulated_sensor_001"
    owner_id = 1
    
    try:
        async with SessionLocal() as db:
            user_res = await db.execute(select(User).order_by(User.id))
            owner = user_res.scalars().first()
            if not owner:
                logger.error("Simulation failed: No users found in database.")
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
            logger.info(f"Simulation device ready: {sim_device_identifier}")
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
                
                if readings["heart_rate"] > 75:
                    await manager.broadcast(json.dumps({
                        "type": "thought_stream",
                        "agent": "IoT-Monitor",
                        "content": f"CRITICAL: Heart rate spike ({readings['heart_rate']} BPM) detected."
                    }))
                    await asyncio.sleep(1)
                    await manager.broadcast(json.dumps({
                        "type": "thought_stream",
                        "agent": "Planner",
                        "content": "Anomalous telemetry detected. Scheduling triage tasks."
                    }))

                await IoTService.process_realtime_data({
                    "device_id": sim_device_identifier,
                    "device_identifier": sim_device_identifier,
                    "user_id": owner_id,
                    "data_type": "sensor_readings",
                    "type": "sensor_readings",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "value": readings
                })
                await manager.broadcast(json.dumps({
                    "type": "iot_update",
                    "device": sim_device_identifier,
                    "data": readings
                }))
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
@router.get("/models/provider-stats/all")
async def get_all_provider_stats(user_id: int = Depends(require_admin)):
    """Return rate limit statistics for all configured providers."""
    providers = ["groq", "ollama", "gemini", "deepseek"]
    stats = {}
    for provider in providers:
        try:
            stats[provider] = await RateLimitService.get_stats(provider)
        except Exception:
            stats[provider] = {"error": "Not configured"}
    return stats

@router.get("/config/ai-provider-settings/all")
async def get_all_provider_settings(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get settings for all AI providers."""
    try:
        stmt = select(SystemConfig).where(SystemConfig.key.like("ai_provider_%"))
        configs = (await db.execute(stmt)).scalars().all()
        
        providers = {}
        for c in configs:
            parts = c.key.split('_')
            if len(parts) >= 4:
                p_name = parts[2]
                setting = "_".join(parts[3:])
                if p_name not in providers:
                    providers[p_name] = {}
                providers[p_name][setting] = c.value
        
        return providers
    except Exception as e:
        logger.error(f"Error getting all provider settings: {e}")
        return {}


