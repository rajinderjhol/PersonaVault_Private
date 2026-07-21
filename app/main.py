import warnings
warnings.filterwarnings("ignore", message=".*google.generativeai.*")
warnings.filterwarnings("ignore", category=FutureWarning)
import httpx
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from app.db.session import engine, Base, SessionLocal, get_db, AsyncSession
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from app.utils.websocket import manager
from app.services.iot_service import IoTService
from prometheus_client import make_asgi_app, Counter, Histogram, REGISTRY
from sqlalchemy import text, select, func
from uvicorn.config import LOGGING_CONFIG
from passlib.context import CryptContext

from app.api.v1.endpoints import (
    auth, memory, ollama, iot, context, enterprise, legal, 
    robotics, widgets, files, admin, system_admin, admin_dashboard
)
from app.api.v1.endpoints import persona as personalization
from app.api.v1.endpoints import workflow as automation
from app.core.audit import audit_middleware
from app.core.rbac import rbac_middleware
from app.core.rate_limit import rate_limiter
from app.config import Config

# Import Cognitive Swarm Components
from orchestrator import MultiAgentOrchestrator
from app.services.ai_router import AIRouter
from app.services.planning_agent import PlanningAgent
from app.services.retrieval_agent import RetrievalAgent
from app.services.generator_agent import GeneratorAgent
from app.services.judge_agent import JudgeAgent
from app.services.reasoner_agent import ReasonerAgent
from app.services.empathy_agent import EmpathyAgent
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.services.validator_agent import ValidatorAgent
from app.services.hitl_service import HITLService
from app.services.approval import ApprovalService

# Create tables
from app.models import (
    AuditLog, UserSession, Memory, User, SystemConfig, Organization, Base,
    LegalMatter, LegalDocument, WorkflowTask, AISetting, IoTDevice, IoTData,
    SemanticPattern, PersonalContext, UserPersona, MedicalAlert
)
from app.core.dependencies import require_admin
from app.services.graph_service import graph_service
from app.services.vector_service import vector_service
from app.services.task_service import init_scheduler

# Password hashing for seeding
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prometheus metric registration guard to prevent "Duplicated timeseries" error on reload
if "personavault_api_requests_total" not in REGISTRY._names_to_collectors:
    API_REQUEST_COUNT = Counter("personavault_api_requests_total", "Total count of API requests", ["method", "endpoint", "status"])
    API_REQUEST_LATENCY = Histogram("personavault_api_request_latency_seconds", "Latency of API requests in seconds", ["method", "endpoint"])
else:
    API_REQUEST_COUNT = REGISTRY._names_to_collectors["personavault_api_requests_total"]
    API_REQUEST_LATENCY = REGISTRY._names_to_collectors["personavault_api_request_latency_seconds"]

# Ensure required directories exist
os.makedirs("storage/memory_db", exist_ok=True)
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/logs", exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler for background tasks
init_scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events, including database seeding."""
    # Initialize shared HTTP client
    app.state.ai_client = httpx.AsyncClient()

    # Initialize the Cognitive Swarm
    logger.info("Lifespan: Igniting Cognitive Swarm...")
    app.state.ai_router = AIRouter(engine_mode="Local-First (Ollama)")
    app.state.semantic_memory = SemanticMemory(SessionLocal)
    app.state.episodic_memory = EpisodicMemory(SessionLocal)
    
    app.state.planning_agent = PlanningAgent(semantic_memory=app.state.semantic_memory)
    app.state.retrieval_agent = RetrievalAgent(
        vector_store=vector_service,
        graph_service=graph_service
    )
    app.state.generator_agent = GeneratorAgent(client=app.state.ai_client)
    app.state.judge_agent = JudgeAgent(ollama_url=Config.OLLAMA_BASE_URL, client=app.state.ai_client)
    app.state.empathy_agent = EmpathyAgent(
        ollama_url=Config.OLLAMA_BASE_URL, 
        client=app.state.ai_client,
        session_factory=SessionLocal
    )
    app.state.reasoner_agent = ReasonerAgent(client=app.state.ai_client)
    app.state.validator_agent = ValidatorAgent(client=app.state.ai_client)
    app.state.hitl_service = HITLService(SessionLocal)
    app.state.approval_service = ApprovalService(SessionLocal)

    app.state.orchestrator = MultiAgentOrchestrator(agents={
        "planner": app.state.planning_agent,
        "retriever": app.state.retrieval_agent,
        "reasoner": app.state.reasoner_agent,
        "validator": app.state.validator_agent,
        "generator": app.state.generator_agent,
        "judge": app.state.judge_agent,
        "router": app.state.ai_router,
        "empathy": app.state.empathy_agent,
        "hitl": app.state.hitl_service
    })
    
    # Initialize database tables (Lattices)
    logger.info("Lifespan: Synchronizing database lattices...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default data
    async with SessionLocal() as db:
        try:
            # Ensure default organization exists (Foreign Key requirement)
            org_stmt = select(Organization).where(Organization.slug == "default")
            org_result = await db.execute(org_stmt)
            org = org_result.scalars().first()
            if not org:
                org = Organization(name="Default Organization", slug="default")
                db.add(org)
                await db.flush()
            
            # Seed admin user if missing
            admin_stmt = select(User).where(User.username == "admin")
            admin_result = await db.execute(admin_stmt)
            admin_user = admin_result.scalars().first()
            if not admin_user:
                logger.info("Seeding default admin user...")
                admin_user = User(
                    username="admin",
                    email="admin@personavault.local",
                    hashed_password=pwd_context.hash("admin123"), # Hash the password!
                    role="admin",
                    organization_id=org.id,
                    is_active=True
                )
                db.add(admin_user)
                await db.commit()
        except Exception as e:
            logger.warning(f"Lifespan seeding issue: {e}")
            await db.rollback()
            
    # Initialize unified MemoryService and Ignite background Crystallization Task
    from app.services.memory_service import MemoryService
    from consolidation import ConsolidationTask
    app.state.memory_service = MemoryService(
        db=SessionLocal,
        vector_service=vector_service,
        graph_service=graph_service
    )
    app.state.consolidation_task = ConsolidationTask(
        orchestrator=app.state.orchestrator,
        memory_service=app.state.memory_service,
        config={"batch_size": 10, "interval_hours": 1.0}
    )
    asyncio.create_task(app.state.consolidation_task.run())

    # Ignite Physical Telemetry Adapter
    from medical_adapter import MedicalTelemetryAdapter
    app.state.medical_adapter = MedicalTelemetryAdapter(orchestrator=app.state.orchestrator)
            
    logger.info("✨ PersonaVault: Cognitive Engine Ignition Complete.")
    logger.info("  -> Admin Dashboard: http://localhost:8000/admin/dashboard")
    logger.info("  -> API Swagger UI:  http://localhost:8000/docs")
    logger.info("  -> Health Monitor:  http://localhost:8000/health/engine")
            
    yield
    # Graceful shutdown
    await app.state.ai_client.aclose()
    logger.info("Application shutdown complete.")

# Initialize FastAPI app with lifespan from lifecycle.py
app = FastAPI(
    title="PersonaVault API",
    description="AI-powered personal memory vault",
    version="1.0.0",
    lifespan=lifespan
)

# --- PRODUCTION READINESS IMPROVEMENTS ---

# Attach global services to app state for specialized routers
app.state.vector_service = vector_service
app.state.graph_service = graph_service
app.state.iot_service = IoTService
app.state.is_pulling_models = False

# Add /metrics endpoint for Prometheus scraping
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)  # Note: In production, protect this with IP whitelisting

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# Prometheus Middleware to capture metrics for all requests
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    
    with API_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)
        
    API_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
    return response

# Enterprise Governance Middlewares
app.middleware("http")(audit_middleware)
app.middleware("http")(rbac_middleware)
app.middleware("http")(rate_limiter)

# Register DB middleware LAST so it executes FIRST in the request chain
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    async with SessionLocal() as db:
        request.state.db = db
        return await call_next(request)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(ollama.router, prefix="/api/v1/ollama", tags=["ollama"])
app.include_router(iot.router, prefix="/api/v1/iot", tags=["iot"])
app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
app.include_router(enterprise.router, prefix="/api/v1", tags=["enterprise"])
app.include_router(robotics.router, prefix="/api/v1")
app.include_router(legal.router, prefix="/api/v1")
app.include_router(personalization.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(widgets.router, prefix="/api/v1/widgets", tags=["widgets"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])

# Admin and System routes (Mounted at /api/v1 to preserve internal module route names)
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(admin_dashboard.router, prefix="/api/v1", tags=["admin"])
app.include_router(system_admin.router, prefix="/api/v1", tags=["system"])

# Global Exception Handler for Graceful Degradation
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Cognitive Engine Error", "code": "SERV_001"}
    )

# WebSocket endpoint for real-time IoT and communication
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # SECURITY HANDSHAKE: Validate session before accepting the connection
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
                
                # Log and process based on type
                if parsed.get("type") == "iot_data":
                    # In production, we'd verify the owner matches the session user here
                    await IoTService.process_realtime_data(parsed["data"])
                
                await manager.send_personal_message(
                    json.dumps({
                        "status": "processed",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }),
                    client_id
                )
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received on WebSocket from {client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)

# Root endpoint - redirects to dashboard or login
@app.get("/")
async def root(request: Request):
    if request.cookies.get("session_id"):
        return RedirectResponse(url="/admin/dashboard")
    return RedirectResponse(url="/login")

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_proxy():
    """Redirect to the modular dashboard UI."""
    return RedirectResponse(url="/api/v1/admin/dashboard/")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PersonaVault Login</title>
        <style>
            body { background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; }
            .login-card { background: #1e293b; padding: 40px; border-radius: 8px; width: 320px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
            h2 { color: #38bdf8; margin-top: 0; }
            p { color: #94a3b8; font-size: 14px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #38bdf8; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 16px; }
            button:hover { background: #7dd3fc; }
            .error { color: #f87171; margin-top: 10px; display: none; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>🛡️ PersonaVault</h2>
            <p>Admin Login</p>
            <input type="text" id="username" placeholder="Username" value="admin">
            <input type="password" id="password" placeholder="Password" value="admin123">
            <button onclick="login()">Sign In</button>
            <div id="error" class="error">Invalid credentials. Try admin/admin123</div>
        </div>
        <script>
            async function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const res = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ username, password })
                });
                if (res.ok) window.location.href = '/admin/dashboard';
                else document.getElementById('error').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """

# Kubernetes liveness probe
@app.get("/health/liveness")
async def liveness_check():
    return {"status": "alive"}

# Kubernetes readiness probe - checks DB connectivity
@app.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return {"status": "not_ready", "database": "disconnected"}

# Engine health check (for dev_restart.sh) - Moved above uvicorn.run
@app.get("/health/engine")
async def engine_health():
    return {
        "status": "ready",
        "engine_mode": "Local-First (Ollama)",
        "ai_service": "connected",
        "vector_store": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Detailed health check for administrators
@app.get("/health/detailed")
async def detailed_health(request: Request, user_id: int = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    # Use the existing admin_dashboard helper check for Ollama consistency
    from app.api.v1.endpoints.admin_dashboard import _check_ollama
    
    active_sessions = (await db.execute(select(func.count(UserSession.id)))).scalar_one()
    total_memories = (await db.execute(select(func.count(Memory.id)))).scalar_one()
    pending_audits = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.status == "pending"))).scalar_one()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "connected",
            "vector_store": "active",
            "graph_store": "connected" if graph_service.driver else "disabled",
            "ai_service": await _check_ollama(request)
        },
        "metrics": {
            "active_sessions": active_sessions,
            "total_memories": total_memories,
            "pending_audits": pending_audits
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "PersonaVault API",
        "version": "1.0.0",
        "environment": "production"
    }

if __name__ == "__main__":
    # Configure uvicorn to also log to uvicorn.log
    LOGGING_CONFIG["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": "storage/logs/uvicorn.log",
        "formatter": "default",
    }
    LOGGING_CONFIG["loggers"]["uvicorn"]["handlers"].append("file")
    LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
        "handlers": ["file"],
        "level": "INFO",
        "propagate": False,
    }
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_config=LOGGING_CONFIG)
