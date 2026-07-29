"""
Modular Dashboard Router - Serves individual tab content
"""
from fastapi import APIRouter, Depends, Request, status, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_
from datetime import datetime, timedelta, timezone
import os
import time
import logging
import json
import psutil
import shutil
import random
import time
import asyncio

from app.core.dependencies import require_admin
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
from app.services.intelligence_gateway import gateway # Import the global gateway instance

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["admin"])

@router.get("/", response_class=HTMLResponse)
async def dashboard_root(request: Request):
    """Serve the main dashboard UI."""
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    base_path = TEMPLATE_DIR / "base.html"
    if base_path.exists():
        with open(base_path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"

def _safe_metric_get(metric, default=0, labels=None):
    try:
        if labels:
            # For prometheus Gauge with labels
            return metric.labels(**labels)._value.get()
        if hasattr(metric, '_value') and hasattr(metric._value, 'get'): return metric._value.get()
        if hasattr(metric, 'value'): return metric.value
        return float(metric) if metric is not None else default
    except: return default

@router.get("/", response_class=HTMLResponse)
async def dashboard_ui(request: Request):
    """Serve the main dashboard UI with modular tabs."""
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Serve the base template
    base_path = TEMPLATE_DIR / "base.html"
    if base_path.exists():
        with open(base_path, "r") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

@router.get("/static/dashboard.css", response_class=HTMLResponse)
async def dashboard_css():
    """Serve the dashboard CSS."""
    css_path = Path(__file__).parent / "static" / "dashboard.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            return HTMLResponse(f.read(), media_type="text/css")
    return HTMLResponse("/* CSS not found */", status_code=404)

@router.get("/tab/{tab_id}", response_class=HTMLResponse)
async def get_tab(tab_id: str, user_id: int = Depends(require_admin)):
    """Serve individual tab content."""
    tab_path = TEMPLATE_DIR / f"{tab_id}.html"
    if tab_path.exists():
        with open(tab_path, "r") as f:
            return HTMLResponse(f.read())
            
    # Fallback content to ensure UI functionality during refactor
    fallbacks = {
        "overview": '<div id="metrics-grid" class="grid"></div><div class="card"><h3 class="card-title">Intelligence Feed</h3><pre id="raw-metrics">Initializing system state...</pre></div>',
        "models": '<div class="card"><h3 class="card-title">Ollama Node</h3><div id="models-list" style="display:flex; flex-direction:column; gap:12px;"></div></div>',
        "logs": '<div class="card" style="height:500px; display:flex; flex-direction:column;"><div id="log-container" class="log-container"></div></div>',
        "agents": '<div class="grid"><div class="card"><div class="card-title">Cognitive Load</div><div id="agent-load-stats" class="mt-10"></div></div><div class="card"><div class="card-title">Empathy & Tone</div><div id="empathy-stats" class="mt-10"></div></div></div><div class="card"><div class="card-title">Human-In-The-Loop</div><div id="hitl-list" class="mt-10"></div></div>',
        "mcp": '<div class="grid"><div class="card"><div class="card-title">Registered Nodes</div><div id="mcp-servers-list" class="mt-10"></div></div><div class="card"><div class="card-title">Available Swarm Tools</div><div id="mcp-tools-list" class="mt-10"></div></div></div>',
        "lattices": '<div class="card" style="margin-bottom: 25px; border-left: 4px solid #a855f7;"><div class="metric-label">Memory Distribution Ratio</div><div class="mem-viz-container"><div id="bar-l2" class="viz-l2" style="width: 10%"></div><div id="bar-l3" class="viz-l3" style="width: 10%"></div></div></div><div class="grid"><div class="card"><div class="metric-label">Layer 1 (Gas)</div><div class="metric-value">Active</div></div><div class="card"><div class="metric-label">Layer 2 (Liquid)</div><div id="layer2-count" class="metric-value">0</div></div><div class="card"><div class="metric-label">Layer 3 (Ice)</div><div id="layer3-count" class="metric-value">0</div></div></div>'
    }
    return HTMLResponse(fallbacks.get(tab_id, f"<div class='metric-label'>Fragment '{tab_id}' not found</div>"))

# ============ Operational Endpoints ============

@router.get("/metrics")
async def get_system_metrics(request: Request, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    now_utc = datetime.now(timezone.utc)
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        res_user_total = await db.execute(select(func.count(User.id)))
        res_iot_points = await db.execute(select(func.count(IoTData.id)).where(IoTData.timestamp >= start_of_day))
        res_mem_total = await db.execute(select(func.count(Memory.id)))
        res_session_active = await db.execute(select(func.count(UserSession.id)).where(UserSession.is_active == True))
        res_iot_active = await db.execute(select(IoTDevice).where(IoTDevice.status == "active"))
        res_legal = await db.execute(select(func.count(LegalMatter.id)).where(LegalMatter.status == "active"))

        active_iot = res_iot_active.scalars().all()
        orchestrator = getattr(request.app.state, "orchestrator", None)

        return {
            "timestamp": now_utc.isoformat(),
            "users": {"total": res_user_total.scalar_one_or_none() or 0},
            "memories": {"total": res_mem_total.scalar_one_or_none() or 0},
            "sessions": {"active": res_session_active.scalar_one_or_none() or 0},
            "iot": {
                "active_count": len(active_iot),
                "active_devices": [d.device_name or d.device_id for d in active_iot],
                "data_points_today": res_iot_points.scalar_one_or_none() or 0
            },
            "legal": {"active_matters": res_legal.scalar_one_or_none() or 0},
            "ai": {
                "ollama_status": "connected" if await _check_ollama(request) else "disconnected",
                "gemini_status": "connected" if await _check_gemini(request) else "not_configured",
                "verilink_offline": getattr(orchestrator, "offline_mode", False)
            },
            "system": {
                "vector_index_size": len(getattr(request.app.state.vector_service, "metadata", [])),
                "thermodynamics": {
                    "crystallization_rate": _safe_metric_get(CRYSTALLIZATION_VELOCITY),
                    "plasma_state": "High-Energy Reasoning Active" if _safe_metric_get(PLASMA_ACTIVE) > 0 else "Stable"
                },
                "storage_used": await _get_storage_usage(),
                "cpu": await _get_cpu_usage(),
                "memory": await _get_memory_usage()
            }
        }
    except Exception as e:
        logger.error(f"Modular metrics error: {e}")
        return {"error": str(e)}

@router.websocket("/ws/{client_id}")
async def dashboard_websocket_endpoint(websocket: WebSocket, client_id: str):
    if websocket.client_state.value == 0: # CONNECTING
        await websocket.accept()

    session_id = websocket.cookies.get("session_id")
    if not session_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(client_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)

@router.get("/cognitive-load")
async def get_agent_load(request: Request, user_id: int = Depends(require_admin)):
    orchestrator = getattr(request.app.state, "orchestrator", None)
    # Get real statuses from AGENT_STATUS metric
    activity = {name: int(_safe_metric_get(AGENT_STATUS, labels={"agent_name": name})) for name in getattr(orchestrator, "agents", {}).keys()}
    return {
        "active_tasks": sum(activity.values()),
        "agent_activity": activity
    }

@router.get("/empathy/status")
async def get_empathy_grounding(request: Request, user_id: int = Depends(require_admin)):
    agent = getattr(request.app.state, "empathy_agent", None)
    if agent:
        return {"mood": getattr(agent, "last_mood", "Calm"), "tone": getattr(agent, "last_tone", "Supportive")}
    return {"mood": "Calm", "tone": "Supportive"}
@router.get("/models")
async def list_models(request: Request, user_id: int = Depends(require_admin)):
    try:
        res = await request.app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
        return res.json()
    except: return {"models": []}

@router.get("/logs/stream")
async def stream_engine_logs(request: Request, user_id: int = Depends(require_admin)):
    log_file = "storage/logs/uvicorn.log"
    async def log_generator():
        if not os.path.exists(log_file):
            yield "data: [SYSTEM] Log file not found.\n\n"; return
        with open(log_file, "r") as f:
            f.seek(0, os.SEEK_END)
            while not await request.is_disconnected():
                line = f.readline()
                if not line: await asyncio.sleep(0.5); continue
                yield f"data: {line.strip()}\n\n"
    return StreamingResponse(log_generator(), media_type="text/event-stream")

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

@router.get("/chat/history")
async def get_chat_history(user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Retrieve recent chat history from episodic memory logs."""
    stmt = select(Memory).where(Memory.tags.like("%interaction_log%")).order_by(Memory.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [{"content": l.content, "timestamp": l.created_at.isoformat()} for l in reversed(logs)]


@router.get("/hitl/pending")
async def list_pending_hitl(user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(PendingAction).where(PendingAction.status == "pending").order_by(PendingAction.created_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    return [{"id": p.id, "agent_type": p.agent_type, "query": p.query, "timestamp": p.created_at.isoformat()} for p in results]

@router.get("/governance/logs")
async def get_governance_logs(user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(EpisodicEntry).order_by(EpisodicEntry.timestamp.desc()).limit(20)
    results = (await db.execute(stmt)).scalars().all()
    return {"logs": [{"id": e.id, "query": e.query or "No query", "receipt": e.governance_receipt_id or "local", "timestamp": e.timestamp.isoformat(), "hitl": e.hitl_approved} for e in results]}

@router.get("/learning/config")
async def get_learning_settings(db: AsyncSession = Depends(get_db), user_id: int = Depends(require_admin)):
    stmt = select(SystemConfig).where(SystemConfig.key.in_(["graduation_batch_size", "graduation_interval_hours"]))
    configs = (await db.execute(stmt)).scalars().all()
    cfg_map = {c.key: c.value for c in configs}
    return {"batch_size": int(cfg_map.get("graduation_batch_size", 10)), "interval_hours": float(cfg_map.get("graduation_interval_hours", 1.0))}

@router.post("/system/simulate-iot")
async def toggle_simulation(request: Request, user_id: int = Depends(require_admin)):
    if hasattr(request.app.state, "iot_sim_task") and request.app.state.iot_sim_task and not request.app.state.iot_sim_task.done():
        request.app.state.iot_sim_task.cancel()
        return {"status": "stopped"}
    request.app.state.iot_sim_task = asyncio.create_task(_run_iot_simulation())
    return {"status": "started"}

@router.post("/governance/toggle-offline")
async def toggle_verilink_offline(request: Request, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if not orchestrator: raise HTTPException(status_code=500, detail="Orchestrator missing")
    new_state = not getattr(orchestrator, "offline_mode", False)

    # Update/Get DB Config
    stmt = select(SystemConfig).where(SystemConfig.key == "verilink_offline_mode")
    config = (await db.execute(stmt)).scalars().first()
    
    # Toggle current state
    val_str = "true" if new_state else "false"
    
    if not config:
        db.add(SystemConfig(key="verilink_offline_mode", value=val_str))
    else:
        config.value = val_str
    
    await db.commit()

    orchestrator.offline_mode = new_state

    if new_state:
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

    return {"status": "success", "offline_mode": new_state}


# ============ BLACKBOARD & SWARM TRACE ============

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


@router.get("/swarm/negotiation-trace")
async def get_negotiation_trace(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Get the real swarm negotiation trace from blackboard history."""
    blackboard = getattr(request.app.state, "blackboard", None)
    if blackboard and blackboard.history:
        history = blackboard.history[-10:] # Recent steps
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

@router.get("/config/primary-ai-provider")
async def get_primary_ai_provider_dashboard(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get the current primary AI provider for the dashboard."""
    stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
    result = await db.execute(stmt)
    config = result.scalars().first()
    return {"primary_provider": config.value if config else "ollama"}

@router.post("/config/primary-ai-provider")
async def update_primary_ai_provider_dashboard(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update the primary AI provider and reload gateway config."""
    data = await request.json()
    provider = data.get("provider")

    stmt = select(SystemConfig).where(SystemConfig.key == "primary_ai_provider")
    result = await db.execute(stmt)
    config = result.scalars().first()
    if not config:
        config = SystemConfig(key="primary_ai_provider", value=provider)
        db.add(config)
    else:
        config.value = provider
    await db.commit()
    await gateway.reload_config() # Trigger the gateway to reload its configuration
    return {"status": "success", "new_primary_provider": provider}

@router.get("/config/ai-provider-settings/{provider}")
async def get_ai_provider_settings(
    provider: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get host and API key for a specific provider."""
    stmt = select(SystemConfig).where(SystemConfig.key.in_([
        f"ai_provider_{provider}_host", 
        f"ai_provider_{provider}_api_key",
        f"ai_provider_{provider}_model"
    ]))
    result = await db.execute(stmt)
    configs = result.scalars().all()
    res = {"host": "", "api_key": "", "model": ""}
    for c in configs:
        if "host" in c.key: res["host"] = c.value
        if "api_key" in c.key: res["api_key"] = c.value
        if "model" in c.key: res["model"] = c.value
    return res

@router.post("/config/ai-provider-settings")
async def update_ai_provider_settings(
    request: Request,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Save cloud API settings and reload gateway."""
    data = await request.json()
    provider = data.get("provider")
    if not provider: raise HTTPException(400, "Provider required")
    
    for key_suffix in ["host", "api_key", "model"]:
        val = data.get(key_suffix)
        db_key = f"ai_provider_{provider}_{key_suffix}"
        stmt = select(SystemConfig).where(SystemConfig.key == db_key)
        config = (await db.execute(stmt)).scalars().first()
        if not config: db.add(SystemConfig(key=db_key, value=str(val or "")))
        else: config.value = str(val or "")

    # Mark as enabled
    en_key = f"ai_provider_{provider}_enabled"
    stmt_en = select(SystemConfig).where(SystemConfig.key == en_key)
    config_en = (await db.execute(stmt_en)).scalars().first()
    if not config_en: db.add(SystemConfig(key=en_key, value="true"))
    else: config_en.value = "true"
    
    await db.commit()
    await gateway.reload_config()
    return {"status": "success"}

@router.get("/config/ai-providers/cloud")
async def list_cloud_providers(db: AsyncSession = Depends(get_db)):
    """List all configured cloud AI providers."""
    stmt = select(SystemConfig).where(SystemConfig.key.like("ai_provider_%"))
    configs = (await db.execute(stmt)).scalars().all()
    providers = {}
    for c in configs:
        parts = c.key.split('_')
        if len(parts) >= 4:
            p_name = parts[2]
            setting = "_".join(parts[3:])
            if p_name not in providers: providers[p_name] = {"name": p_name}
            providers[p_name][setting] = c.value
    # Return list of cloud providers (excluding local ollama)
    return [v for k, v in providers.items() if k != "ollama"]

@router.delete("/config/ai-provider/{provider}")
async def delete_ai_provider(provider: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific AI provider configuration."""
    from sqlalchemy import delete
    stmt = delete(SystemConfig).where(SystemConfig.key.like(f"ai_provider_{provider}_%"))
    await db.execute(stmt)
    await db.commit()
    await gateway.reload_config()
    return {"status": "success"}

@router.post("/config/ai-provider-test")
async def test_ai_provider_connection(
    request: Request,
    user_id: int = Depends(require_admin)
):
    """Test connection for a specific provider with provided credentials."""
    data = await request.json()
    provider = data.get("provider")
    if not provider: raise HTTPException(400, "Provider required")
    
    result = await gateway.test_provider_connection(provider, data.get("host"), data.get("api_key"))
    return result

# ============ Helper Simulation ============

# Add a cache for Ollama status
_ollama_cache = {
    "status": "unknown",
    "last_check": 0,
    "cache_ttl": 30  # Only check every 30 seconds
}

async def _check_ollama(request) -> bool:
    """Check Ollama service status with caching."""
    now = time.time()
    if now - _ollama_cache["last_check"] < _ollama_cache["cache_ttl"]:
        return _ollama_cache["status"]

    try:
        res = await request.app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=1.0)
        if res.status_code == 200:
            models = res.json().get("models", [])
            _ollama_cache["status"] = f"connected ({len(models)} models)" if models else "connected (no models)"
        else:
            _ollama_cache["status"] = "error"
    except Exception as e:
        logger.warning(f"Ollama health check: service unreachable at {Config.OLLAMA_BASE_URL}")
        _ollama_cache["status"] = "disconnected"

    _ollama_cache["last_check"] = now
    return _ollama_cache["status"]

async def _check_gemini(request) -> str:
    """Check Gemini service status."""
    api_key = Config.GEMINI_API_KEY # Use centralized config
    if not api_key:
        return "not_configured"
    try:
        import google.generativeai as genai # type: ignore
        genai.configure(api_key=api_key)
        return "connected"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return "error"

async def _get_storage_usage() -> dict:
    """Get storage usage information."""
    home_dir = os.path.expanduser("~")
    project_dir = Path(__file__).parents[4] # Go up to personavault/backend
    
    def get_dir_size(path):
        total = 0
        if not os.path.exists(path): return 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try: total += os.path.getsize(fp)
                except (FileNotFoundError, PermissionError): continue
        return round(total / (1024**2), 2)  # Return MB

    try:
        total, used, free = shutil.disk_usage(home_dir)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round((used / total) * 100, 2) if total > 0 else 0,
            "breakdown_mb": {
                "venv": get_dir_size(project_dir / ".venv"),
                "uploads": get_dir_size(project_dir / "storage/uploads"),
                "vector_storage": get_dir_size(project_dir / "storage")
            },
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        return {"error": f"Storage diagnostics unavailable: {str(e)}"}

async def _get_cpu_usage() -> float:
    """Get CPU usage."""
    try: return psutil.cpu_percent(interval=None)
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

@router.get("/static/dashboard.css", response_class=HTMLResponse)
async def dashboard_css():
    """Serve the dashboard CSS."""
    css_path = Path(__file__).parent / "static" / "dashboard.css"
    if css_path.exists():
        with open(css_path, "r") as f:
            return HTMLResponse(f.read(), media_type="text/css")
    return HTMLResponse("/* CSS not found */", status_code=404)
