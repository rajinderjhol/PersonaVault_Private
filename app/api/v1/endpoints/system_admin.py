import os
import asyncio
import logging
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from datetime import datetime
from app.config import Config
from app.core.dependencies import require_admin
from app.models import SystemConfig, UserSession, Memory, AuditLog

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/logs/stream")
async def stream_logs(request: Request, user_id: int = Depends(require_admin)):
    log_file = "storage/logs/uvicorn.log"
    async def log_generator():
        if not os.path.exists(log_file):
            yield "data: [SYSTEM] Log file not found.\n\n"; return
        with open(log_file, "r") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 4096))
            lines = f.readlines()
            for line in lines[-25:]: yield f"data: {line.strip()}\n\n"
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.4)
                    if await request.is_disconnected(): break
                    continue
                yield f"data: {line.strip()}\n\n"
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@router.get("/admin/models")
async def list_models(request: Request, user_id: int = Depends(require_admin)):
    try:
        res = await request.app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
        return res.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.post("/admin/models/pull")
async def pull_model_endpoint(request: Request, user_id: int = Depends(require_admin)):
    body = await request.json()
    model_name = body.get("name")
    if not model_name: return JSONResponse(status_code=400, content={"detail": "Model name required"})
    async def pull_generator():
        async with request.app.state.ai_client.stream("POST", f"{Config.OLLAMA_BASE_URL}/api/pull", json={"name": model_name}, timeout=None) as response:
            async for chunk in response.aiter_text(): yield f"data: {chunk}\n\n"
    return StreamingResponse(pull_generator(), media_type="text/event-stream")

@router.delete("/admin/models/{model_name}")
async def delete_model_endpoint(request: Request, model_name: str, user_id: int = Depends(require_admin)):
    try:
        res = await request.app.state.ai_client.request("DELETE", f"{Config.OLLAMA_BASE_URL}/api/delete", json={"name": model_name})
        return {"status": "success", "ollama_response": res.status_code}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/admin/learning/config")
async def get_learning_config(request: Request, user_id: int = Depends(require_admin)):
    task = request.app.state.consolidation_task
    return {"batch_size": getattr(task, "batch_size", 10), "interval_hours": getattr(task, "interval_hours", 1.0)}

@router.post("/admin/learning/config")
async def update_learning_config(request: Request, user_id: int = Depends(require_admin)):
    body = await request.json(); task = request.app.state.consolidation_task; db = request.state.db
    if "batch_size" in body:
        val = int(body["batch_size"]); task.batch_size = val
        cfg = (await db.execute(select(SystemConfig).where(SystemConfig.key == "graduation_batch_size"))).scalars().first()
        if cfg: cfg.value = str(val)
        else: db.add(SystemConfig(key="graduation_batch_size", value=str(val)))
    if "interval_hours" in body:
        val = float(body["interval_hours"]); task.interval_hours = val
        cfg = (await db.execute(select(SystemConfig).where(SystemConfig.key == "graduation_interval"))).scalars().first()
        if cfg: cfg.value = str(val)
        else: db.add(SystemConfig(key="graduation_interval", value=str(val)))
    await db.commit()
    return {"status": "success"}

@router.post("/admin/learning/trigger")
async def trigger_learning(request: Request, user_id: int = Depends(require_admin)):
    if hasattr(request.app.state.consolidation_task, 'trigger_event'):
        request.app.state.consolidation_task.trigger_event.set()
    return {"status": "success"}

@router.get("/admin/governance/status")
async def get_governance_status(request: Request, user_id: int = Depends(require_admin)):
    orchestrator = request.app.state.orchestrator
    return {"active": orchestrator.governance is not None, "api_url": "http://localhost:8000", "recent_receipts": getattr(orchestrator, "recent_receipts", [])}

@router.get("/admin/governance/constitution")
async def get_governance_constitution(user_id: int = Depends(require_admin)):
    import json
    try:
        with open("governance_constitution.json", "r") as f: return json.load(f)
    except Exception: return []

@router.post("/admin/governance/constitution")
async def update_governance_constitution(request: Request, user_id: int = Depends(require_admin)):
    import json; body = await request.json()
    try:
        with open("governance_constitution.json", "w") as f: json.dump(body, f, indent=4)
        request.app.state.orchestrator.reload_constitution()
        return {"status": "success"}
    except Exception as e: return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/admin/telemetry/health")
async def get_health_telemetry(request: Request, user_id: int = Depends(require_admin)):
    return getattr(request.app.state, "medical_adapter", None).last_reading if hasattr(request.app.state, "medical_adapter") else {}

@router.get("/admin/hitl/pending")
async def list_pending_hitl(request: Request, user_id: int = Depends(require_admin)):
    return [{"id": "hitl_9901", "agent_type": "ValidatorAgent", "query": "Lattice access request", "reason": "Low confidence", "timestamp": datetime.utcnow().isoformat()}]

@router.get("/admin/mcp/tools")
async def list_mcp_tools(request: Request, user_id: int = Depends(require_admin)):
    server = getattr(request.app.state, "mcp_server", None)
    return await server.list_tools() if server else []

@router.get("/admin/empathy/status")
async def get_empathy_status(request: Request, user_id: int = Depends(require_admin)):
    agent = request.app.state.empathy_agent
    return {"mood": getattr(agent, "last_mood", "unknown"), "tone": getattr(agent, "last_tone", "neutral")}

@router.get("/admin/cognitive-load")
async def get_cognitive_load(request: Request, user_id: int = Depends(require_admin)):
    orchestrator = request.app.state.orchestrator
    return {"active_tasks": getattr(orchestrator, "active_tasks", 0), "agent_activity": getattr(orchestrator, "agent_activity", {})}