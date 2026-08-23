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

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["admin"])
router.include_router(model_router)
router.include_router(metrics_router)
router.include_router(governance_router)
router.include_router(config_router)
router.include_router(maintenance_router)
router.include_router(learning_router)
router.include_router(blackboard_router)
router.include_router(swarm_router)
TEMPLATE_DIR = Path(__file__).parent / "templates"


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
async def dashboard_ui(request: Request):
    """Serve the main dashboard UI with modular tabs."""
    if not request.cookies.get("session_id"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Ensure template directory exists
    if not TEMPLATE_DIR.exists():
        logger.error(f"Template directory not found: {TEMPLATE_DIR}")
        return HTMLResponse("<h1>Dashboard templates missing</h1>", status_code=500)

    base_path = TEMPLATE_DIR / "base.html"
    if not base_path.exists():
        logger.error(f"Dashboard base template not found: {base_path}")
        return HTMLResponse("<h1>Dashboard template 'base.html' not found</h1>", status_code=404)
        
    try:
        with open(base_path, "r") as f:
            return HTMLResponse(f.read())
    except Exception as e:
        logger.error(f"Error reading dashboard template: {e}")
        return HTMLResponse("<h1>Error loading dashboard</h1>", status_code=500)


@router.get("/tab/{tab_id}", response_class=HTMLResponse)
async def get_tab(tab_id: str, user_id: int = Depends(require_admin)):
    """Serve individual tab content with basic include support."""
    tab_path = TEMPLATE_DIR / f"{tab_id}.html"
    if tab_path.exists():
        with open(tab_path, "r") as f:
            content = f.read()
            # Robust include support
            import re
            include_pattern = re.compile(r'{%\s*include\s+[\'\"]evidence_widget\.html[\'\"]\s*%}', re.IGNORECASE)
            if include_pattern.search(content):
                widget_path = TEMPLATE_DIR / "evidence_widget.html"
                if widget_path.exists():
                    with open(widget_path, "r") as wf:
                        content = include_pattern.sub(wf.read(), content)
            return HTMLResponse(content)
    
    fallbacks = {
        "overview": '<div id="metrics-grid" class="grid"></div><div class="card"><h3 class="card-title">Intelligence Feed</h3><pre id="raw-metrics">Initializing system state...</pre></div>',
        "models": '<div class="card"><h3 class="card-title">Ollama Node</h3><div id="models-list" style="display:flex; flex-direction:column; gap:12px;"></div></div>',
        "logs": '<div class="card" style="height:500px; display:flex; flex-direction:column;"><div id="log-container" class="log-container"></div></div>',
        "agents": '<div class="grid"><div class="card"><div class="card-title">Cognitive Load</div><div id="agent-load-stats" class="mt-10"></div></div><div class="card"><div class="card-title">Empathy & Tone</div><div id="empathy-stats" class="mt-10"></div></div></div><div class="card"><div class="card-title">Human-In-The-Loop</div><div id="hitl-list" class="mt-10"></div></div>',
        "mcp": '<div class="grid"><div class="card"><div class="card-title">Registered Nodes</div><div id="mcp-servers-list" class="mt-10"></div></div><div class="card"><div class="card-title">Available Swarm Tools</div><div id="mcp-tools-list" class="mt-10"></div></div></div>',
        "lattices": '<div class="card" style="margin-bottom: 25px; border-left: 4px solid #a855f7;"><div class="metric-label">Memory Distribution Ratio</div><div class="mem-viz-container"><div id="bar-l2" class="viz-l2" style="width: 10%"></div><div id="bar-l3" class="viz-l3" style="width: 10%"></div></div></div><div class="grid"><div class="card"><div class="metric-label">Layer 1 (Gas)</div><div class="metric-value">Active</div></div><div class="card"><div class="metric-label">Layer 2 (Liquid)</div><div id="layer2-count" class="metric-value">0</div></div><div class="card"><div class="metric-label">Layer 3 (Ice)</div><div id="layer3-count" class="metric-value">0</div></div></div>',
        "evidence": '<div class="card"><h3 class="card-title">Evidence Pipeline</h3><div id="evidence-stats-container">Loading...</div></div>'
    }
    return HTMLResponse(fallbacks.get(tab_id, f"<div class='metric-label'>Fragment '{tab_id}' not found</div>"))
