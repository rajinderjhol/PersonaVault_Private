from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
import asyncio
import json
import os
from datetime import datetime, timezone

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models import User, IoTDevice, IoTData, LegalMatter, UserSession, Memory
from app.utils.websocket import manager
from app.services.custom import AGENT_STATUS, CRYSTALLIZATION_VELOCITY, PLASMA_ACTIVE
from app.services.temporal_analysis_service import TemporalAnalysisService
from app.api.v1.endpoints.dashboard.utils import (
    _safe_metric_get, _check_ollama, _check_gemini, _get_storage_usage, 
    _get_cpu_usage, _get_memory_usage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["admin"])

@router.get("/temporal/metrics")
async def get_temporal_metrics(
    time_range: str = Query("30d"),
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        temporal_service = TemporalAnalysisService(db)
        # Simplify date range calculation for now
        days = int(time_range.replace('d', ''))
        
        # Calculate velocity
        velocity_data = await temporal_service.calculate_decision_velocity(
            user_id=user_id.id,
            days=days
        )
        
        # Mocking the rest of the expected data structure for TemporalIntelligenceWidget
        return {
            "velocity": velocity_data.get("velocity", 0.0),
            "decayRate": 0.1,
            "agingPatterns": 0,
            "trendData": {
                "dates": ["Day 1", "Day 15", "Day 30"],
                "values": [0.2, 0.5, velocity_data.get("velocity", 0.0)]
            },
            "patternHealth": {
                "healthy": 10,
                "decaying": 2,
                "critical": 0
            }
        }
    except Exception as e:
        logger.error(f"Temporal metrics error: {e}")
        return {"error": str(e)}

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
    logger.info(f"WebSocket connection attempt for {client_id}")
    if websocket.client_state.value == 0:
        await websocket.accept()

    session_id = websocket.cookies.get("session_id")
    logger.info(f"WebSocket auth session_id: {session_id}")
    if not session_id:
        logger.warning(f"WebSocket auth failed for {client_id}: No session_id cookie.")
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

@router.get("/logs/stream")
async def stream_engine_logs(request: Request, user_id: int = Depends(require_admin)):
    log_file = "storage/logs/uvicorn.log"
    async def log_generator():
        if not os.path.exists(log_file):
            yield "data: [SYSTEM] Log file not found.\n\n"
            return
        with open(log_file, "r") as f:
            f.seek(0, os.SEEK_END)
            while not await request.is_disconnected():
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                yield f"data: {line.strip()}\n\n"
    return StreamingResponse(log_generator(), media_type="text/event-stream")
