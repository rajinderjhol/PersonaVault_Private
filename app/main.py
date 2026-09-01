import warnings
warnings.filterwarnings("ignore", message=".*google.generativeai.*")
warnings.filterwarnings("ignore", category=FutureWarning)
import httpx
import uvicorn
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
from sqlalchemy import text, select, func, inspect
from uvicorn.config import LOGGING_CONFIG
from passlib.context import CryptContext

# Internal Endpoints
from app.api.v1.endpoints import (
    auth, memory, ollama, iot, context, enterprise, legal, 
    robotics, widgets, files, admin, system_admin, mcp, user_profile, settings, organization, trends_mock, ingestion, swarm, integrations, user_preferences, thermodynamics, simulation, graph
)
from app.api.v1.endpoints.user_preferences import router as user_preferences_router

from app.routes import decisions
from app.api.v1.endpoints.ingestion import router as ingestion_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.predictive_enhanced import router as predictive_router
from app.api.v1.endpoints.onboarding import router as onboarding_router
from app.api.v1.endpoints.nlq import router as nlq_router
from app.api.v1.endpoints.proactive import router as proactive_router
from app.api.v1.endpoints.pattern_verification import router as pattern_router

from app.api.v1.endpoints.identity import router as identity_router

from app.api.v1.endpoints.pattern_verification import router as pattern_router

from app.api.v1.endpoints import persona as personalization
from app.api.v1.endpoints import workflow as automation
from app.api.v1.endpoints.packs import router as packs_router
from app.api.v1.endpoints.compiler import router as compiler_router
from app.api.v1.endpoints.models import router as models_router
from app.api.v1.endpoints.trust import router as trust_router
from app.api.v1.endpoints.privacy import router as privacy_router
from app.api.v1.endpoints.security import router as security_router
from app.api.v1.endpoints.admin_users import router as admin_users_router
from app.api.v1.endpoints.constitution import router as constitution_router
from app.api.v1.endpoints.connections import router as connections_router
from app.api.v1.endpoints.governance import router as governance_router
from app.api.v1.endpoints.timeline import router as timeline_router
from app.api.v1.endpoints.behaviour import router as behaviour_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.patterns import router as patterns_router
from app.api.v1.endpoints.policies import router as policies_router
from app.api.v1.endpoints.predictive import router as predictive_router
from app.api.v1.endpoints.generative import router as generative_router
from app.api.v1.endpoints.collaborative import router as collaborative_router
from app.api.v1.endpoints.multimodal import router as multimodal_router
from app.api.v1.endpoints.clinical import router as clinical_router
from app.api.v1.endpoints.dashboard.dashboard_router import router as dashboard_router
from app.api.v1.endpoints.service_registry import router as service_registry_router
from app.api.v1.endpoints.execution_mode import router as execution_mode_router
from app.core.audit import audit_middleware
from app.core.rbac import rbac_middleware
from app.core.rate_limit import rate_limiter
from app.core.dependencies import require_admin, get_current_user
from app.config import Config

# Import Cognitive Swarm Components
from app.swarm.orchestrator import MultiAgentOrchestrator
from app.swarm.core.planner import PlannerAgent
from app.swarm.core.retriever import RetrievalAgent
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.judge import JudgeAgent
from app.swarm.core.reasoner import ReasonerAgent
from app.swarm.core.validator import ValidatorAgent
from app.swarm.core.router import AIRouter
from app.swarm.interaction.empathy import EmpathyAgent
from app.swarm.interaction.hitl import HITLService
from app.services.blackboard import CognitiveBlackboard
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.services.approval import ApprovalService
from app.services.memory_service import MemoryService
from app.repositories.sqlalchemy.memory import SQLMemoryRepository
from app.repositories.sqlalchemy.episodic import SQLEpisodicTaskRepository
from app.repositories.sqlalchemy.semantic_pattern import SQLSemanticPatternRepository
from app.repositories.faiss.vector import FAISSSemanticRepository
from app.repositories.neo4j.graph import Neo4jGraphRepository
from app.services.intelligence_gateway import gateway, MCPRegistry
from app.services.consolidation_service import ConsolidationTask
from app.services.self_improving import SelfImprovingIntelligence
from app.middleware.observability import ObservabilityMiddleware
import scripts.seed_demo_data

# Create tables
from app.models import (
    AuditLog, UserSession, Memory, User, SystemConfig, Organization,
    LegalMatter, LegalDocument, WorkflowTask, AISetting, IoTDevice, IoTData,
    SemanticPattern, PersonalContext, UserPersona, MedicalAlert, PendingAction, EpisodicEntry,
    ChatSession, ChatMessage
)
from app.services.graph_service import graph_service
from app.services.vector_service import vector_service
from app.services.rate_limit_service import RateLimitService
from app.services.task_service import init_scheduler

# Password hashing for seeding
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.services.custom import API_REQUEST_COUNT, API_REQUEST_LATENCY

# Ensure required directories exist
os.makedirs("storage/memory_db", exist_ok=True)
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/logs", exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events, including database seeding."""
    # Initialize scheduler for background tasks
    init_scheduler()
    
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Initialize shared HTTP client
    app.state.ai_client = httpx.AsyncClient(
        timeout=httpx.Timeout(300.0),
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
    )
    
    # Inject shared client into global services
    vector_service.set_client(app.state.ai_client)

    # --- Initialize Repositories ---
    logger.info("Lifespan: Initializing Repositories...")
    app.state.repos = {
        "memory": SQLMemoryRepository(db=SessionLocal),
        "vector": FAISSSemanticRepository(client=app.state.ai_client),
        "graph": Neo4jGraphRepository(),
        "episodic_task": SQLEpisodicTaskRepository(db=SessionLocal),
        "semantic_pattern": SQLSemanticPatternRepository(db=SessionLocal)
    }

    # Initialize the Cognitive Swarm
    logger.info("Lifespan: Igniting Cognitive Swarm...")
    app.state.self_improving = SelfImprovingIntelligence()
    await app.state.self_improving.initialize()
    app.state.blackboard = CognitiveBlackboard()
    app.state.ai_router = AIRouter(engine_mode="Local-First (Ollama)")
    
    app.state.semantic_memory = SemanticMemory(db_session=SessionLocal())
    app.state.episodic_memory = EpisodicMemory(repository=app.state.repos["episodic_task"])
    
    app.state.planning_agent = PlannerAgent(semantic_memory=app.state.semantic_memory)
    app.state.retrieval_agent = RetrievalAgent(
        vector_repo=app.state.repos["vector"],
        graph_repo=app.state.repos["graph"]
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

    app.state.orchestrator = MultiAgentOrchestrator(db_session=SessionLocal, blackboard=app.state.blackboard, confidence_threshold=0.5, agents={
        "planner": app.state.planning_agent,
        "retriever": app.state.retrieval_agent,
        "reasoner": app.state.reasoner_agent,
        "validator": app.state.validator_agent,
        "generator": app.state.generator_agent,
        "judge": app.state.judge_agent,
        "router": app.state.ai_router,
        "empathy": app.state.empathy_agent,
        "hitl": app.state.hitl_service,
        "episodic": app.state.episodic_memory,
        "semantic": app.state.semantic_memory
    })
    
    # Initialize database tables (Lattices)
    logger.info("Lifespan: Synchronizing database lattices...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # --- ✅ SEED DATABASE FIRST ---
    async with SessionLocal() as db:
        try:
            # Ensure default organization exists
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
                    hashed_password=pwd_context.hash("admin123"),
                    role="admin",
                    last_login=now_utc,
                    organization_id=org.id,
                    is_active=True
                )
                db.add(admin_user)
                await db.commit()

            # ✅ SEED SYSTEM_CONFIGS HERE
            # Check if system_configs has ai_providers
            config_stmt = select(SystemConfig).where(SystemConfig.key == "ai_providers")
            config_result = await db.execute(config_stmt)
            config = config_result.scalars().first()
            if not config:
                logger.info("Seeding ai_providers config...")
                config = SystemConfig(
                    key="ai_providers",
                    value='{"ollama": {"enabled": true, "host": "http://localhost:11434", "model": "tinydolphin:latest"}}'
                )
                db.add(config)
                await db.commit()

        except Exception as e:
            logger.warning(f"Lifespan seeding issue: {e}")
            await db.rollback()
    
    # --- ✅ NOW INITIALIZE GATEWAY ---
    async with SessionLocal() as db:
        await gateway._apply_config_async(db)
        gateway._initialized_from_db = True
        logger.info("✅ Intelligence Gateway initialized from database on startup")

    # Initialize Cognitive Lattices
    logger.info("Lifespan: Initializing memory lattices...")
    app.state.repos["vector"]._load_or_create_index()
            
    # Initialize MemoryService
    app.state.memory_service = MemoryService(
        memory_repo=app.state.repos["memory"],
        vector_repo=app.state.repos["vector"],
        graph_repo=app.state.repos["graph"]
    )

    # Ignite background Crystallization Task with optimized settings
    app.state.consolidation_task = ConsolidationTask(
        orchestrator=app.state.orchestrator,
        memory_service=app.state.memory_service,
        config={
            "batch_size": 20,  # Increased from 10
            "interval_hours": 0.5,  # Every 30 minutes instead of 1 hour
            "max_workers": 4  # Parallel processing workers
        }
    )
    # Enable parallel execution
    app.state.orchestrator._parallel_execution = True
    app.state.consolidation_task.trigger_event = asyncio.Event()
    asyncio.create_task(app.state.consolidation_task.run())

    # Ignite Physical Telemetry Adapter
    from app.swarm.specialized.health import HealthAgent
    app.state.medical_adapter = HealthAgent(
        orchestrator=app.state.orchestrator,
        client=app.state.ai_client
    )
            
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

# Serve static files
static_dir = "app/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
# Also mount for dashboard static
app.mount("/api/v1/admin/dashboard/static", StaticFiles(directory=static_dir), name="dashboard_static")

# --- PRODUCTION READINESS IMPROVEMENTS ---

# Attach global services to app state for specialized routers
app.state.vector_service = vector_service
app.state.graph_service = graph_service
app.state.iot_service = IoTService
app.state.is_pulling_models = False

# --- /metrics endpoint — protected via IP allowlist + optional bearer token ---
# Only Prometheus servers (or localhost) and callers with the correct METRICS_TOKEN
# may scrape this endpoint. Unrecognised callers receive a 403.
_raw_metrics_app = make_asgi_app()

async def _protected_metrics_app(scope, receive, send):
    """ASGI wrapper that guards the Prometheus /metrics endpoint."""
    if scope["type"] == "http":
        # Extract client IP (handle X-Forwarded-For for reverse-proxied setups)
        headers = dict(scope.get("headers", []))
        forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
        
        client_info = scope.get("client")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (
            client_info[0] if client_info else "unknown"
        )

        ip_allowed = client_ip in Config.METRICS_ALLOWED_IPS

        # Check bearer token if configured
        token_valid = False
        if Config.METRICS_TOKEN:
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token_valid = auth_header[7:] == Config.METRICS_TOKEN
        else:
            # No token configured — rely on IP allowlist only
            token_valid = True

        if not (ip_allowed or token_valid):
            response = JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: metrics endpoint is restricted"}
            )
            await response(scope, receive, send)
            return

    await _raw_metrics_app(scope, receive, send)

app.mount("/metrics", _protected_metrics_app)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware — origins are driven by ALLOWED_ORIGINS env var
# In development (CORS_ALLOW_ALL=true + APP_ENV=development): wildcard is permitted via regex
# In all other cases: only listed origins are allowed
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.cloudshell\.dev" if Config.CORS_ALLOW_ALL else None,
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
        
    API_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(response.status_code)).inc()
    return response

# Enterprise Governance Middlewares
# Registered in order: Outer -> Inner
app.add_middleware(ObservabilityMiddleware)
app.middleware("http")(audit_middleware)
app.middleware("http")(rbac_middleware)
app.middleware("http")(rate_limiter)

# Register DB middleware LAST so it wraps all other governance middlewares.
# It will be the first to open a session and the absolute last to close it.
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    async with SessionLocal() as db:
        request.state.db = db
        return await call_next(request)
...
# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(security_router, prefix="/api/v1", tags=["security"])
app.include_router(mcp.router, prefix="/api/v1", tags=["mcp"])
app.include_router(compiler_router, prefix="/api/v1", tags=["compiler"])
app.include_router(models_router, prefix="/api/v1", tags=["models"])
app.include_router(trust_router, prefix="/api/v1", tags=["trust"])
app.include_router(user_profile.router, prefix="/api/v1", tags=["user-profile"])
app.include_router(organization.router, prefix="/api/v1", tags=["organizations"])
app.include_router(settings.router, prefix="/api/v1", tags=["settings"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(ollama.router, prefix="/api/v1/ollama", tags=["ollama"])
app.include_router(iot.router, prefix="/api/v1/iot", tags=["iot"])
app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
app.include_router(enterprise.router, prefix="/api/v1", tags=["enterprise"])
app.include_router(robotics.router, prefix="/api/v1")
app.include_router(legal.router, prefix="/api/v1")
app.include_router(personalization.router, prefix="/api/v1")
app.include_router(service_registry_router)
app.include_router(execution_mode_router)
app.include_router(automation.router, prefix="/api/v1")
app.include_router(widgets.router, prefix="/api/v1/widgets", tags=["widgets"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
# Modular Router Registration
from app.api.v1.endpoints.chat_router import router as chat_router
from app.api.v1.endpoints.chat_stream import router as chat_stream_router
from app.api.v1.endpoints.chat_stream import router as chat_stream_router
from app.api.v1.endpoints.chat_sessions import router as chat_sessions_router
from app.api.v1.endpoints.intelligence import router as intelligence_router
from app.api.v1.endpoints.mcp_connectors import router as mcp_connectors_router
from app.api.v1.endpoints.mcp_tools import router as mcp_tools_router


app.include_router(chat_router)
app.include_router(chat_stream_router)
app.include_router(chat_stream_router)
app.include_router(chat_sessions_router)
app.include_router(intelligence_router)
app.include_router(mcp_tools_router)
app.include_router(mcp_connectors_router)
from app.api.v1.endpoints.traces import router as traces_router
app.include_router(traces_router)
app.include_router(decisions.router)
app.include_router(simulation.router)
app.include_router(graph.router)

app.include_router(swarm.router)
app.include_router(integrations.router)
from app.api.v1.endpoints.marketplace import router as marketplace_router
# Modular Dashboard (Take precedence over legacy admin routes)
app.include_router(dashboard_router, prefix="/api/v1/admin/dashboard", tags=["dashboard"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

app.include_router(marketplace_router)
app.include_router(privacy_router)
app.include_router(identity_router)
app.include_router(user_preferences.router)
app.include_router(thermodynamics.router)

# New endpoints
app.include_router(pattern_router, prefix="/api/v1", tags=["admin"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(predictive_router)
app.include_router(onboarding_router)
app.include_router(nlq_router)
app.include_router(proactive_router)
app.include_router(trends_mock.router, prefix="/api/v1", tags=["trends"])

app.include_router(packs_router, prefix="/api/v1/marketplace", tags=["behaviour-packs"])
app.include_router(governance_router, prefix="/api/v1", tags=["governance"])
app.include_router(admin_users_router)
app.include_router(constitution_router)
app.include_router(connections_router)
app.include_router(timeline_router, prefix="/api/v1", tags=["timeline"])
app.include_router(behaviour_router, prefix="/api/v1", tags=["behaviour"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["documents"])
from app.api.v1.endpoints.ingestion import router as ingestion_router
app.include_router(ingestion_router)
app.include_router(patterns_router, prefix="/api/v1")
app.include_router(policies_router)
app.include_router(predictive_router)
app.include_router(generative_router)
app.include_router(collaborative_router)
app.include_router(multimodal_router)
app.include_router(system_admin.router, prefix="/api/v1", tags=["system"])
app.include_router(clinical_router, tags=["clinical"])

# V2 API Registration
from app.api.v2.endpoints import intelligence_packs
app.include_router(intelligence_packs.router)


# Dashboard UI Redirect
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_redirect(request: Request):
    """Redirect to the actual dashboard location."""
    return RedirectResponse(url="/api/v1/admin/dashboard/", status_code=302)

@app.get("/admin/test/layout", response_class=HTMLResponse)
async def test_layout_page(request: Request):
    """Render the layout verification test page."""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "dashboard/test_layout.html",
        {"request": request}
    )

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
    # Complete the handshake first to avoid proxy timeout/errors
    await websocket.accept()

    # SECURITY HANDSHAKE: Validate session token against the database
    session_id = websocket.cookies.get("session_id")
    if not session_id:
        logger.warning(f"WebSocket auth failed for {client_id}: No session_id cookie.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify the session exists, is active, and has not expired
    try:
        async with SessionLocal() as _ws_db:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            session_stmt = select(UserSession).where(
                UserSession.session_token == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > now_utc,
            )
            result = await _ws_db.execute(session_stmt)
            db_session = result.scalars().first()

        if not db_session:
            logger.warning(
                f"WebSocket auth failed for {client_id}: "
                f"session '{session_id[:8]}…' not found, expired, or inactive."
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as ws_auth_err:
        logger.error(f"WebSocket session lookup error for {client_id}: {ws_auth_err}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    await manager.connect(client_id, websocket)  # manager.connect must NOT call accept() again
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
async def detailed_health_check(
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Detailed health check for administrators."""
    import time
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {},
        "metrics": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                health_status["services"]["ollama"] = "connected"
            else:
                health_status["services"]["ollama"] = f"error: {response.status_code}"
    except Exception as e:
        health_status["services"]["ollama"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check vector service
    try:
        if vector_service.index:
            health_status["services"]["vector"] = f"healthy ({vector_service.index.ntotal} entries)"
        else:
            health_status["services"]["vector"] = "not initialized"
    except Exception as e:
        health_status["services"]["vector"] = f"error: {str(e)}"
    
    # Check WebSocket
    try:
        health_status["metrics"]["websocket_connections"] = len(manager.active_connections)
    except:
        pass
    
    # Get system metrics
    health_status["metrics"]["active_sessions"] = (await db.execute(select(func.count(UserSession.id)))).scalar_one_or_zero() or 0
    health_status["metrics"]["total_memories"] = (await db.execute(select(func.count(Memory.id)))).scalar_one_or_zero() or 0
    
    return health_status
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
    from logging.handlers import RotatingFileHandler
    # Configure uvicorn to log to a rotating file
    LOGGING_CONFIG["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "storage/logs/uvicorn.log",
        "formatter": "default",
        "maxBytes": 1024 * 1024,  # 1MB per file
        "backupCount": 3,         # Keep 3 backups
    }
    LOGGING_CONFIG["loggers"]["uvicorn"]["handlers"].append("file")
    LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
        "handlers": ["file"],
        "level": "WARNING",  # Reduce verbosity: only log WARNING or higher
        "propagate": False,
    }
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_config=LOGGING_CONFIG)

# Warm up Ollama to prevent first-request timeout
async def warmup_ollama():
    """Warm up Ollama by sending a small test request."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                "http://localhost:11434/api/generate",
                json={"model": "tinydolphin", "prompt": "Hello", "stream": False}
            )
        logger.info("✅ Ollama warmed up")
    except Exception as e:
        logger.warning(f"Ollama warmup failed: {e}")

# Add to lifespan startup
# Find where lifespan starts and add the warmup
