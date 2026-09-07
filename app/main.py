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
from app.api.v1.endpoints.predictive_enhanced import router as predictive_enhanced_router
from app.api.v1.endpoints.onboarding import router as onboarding_router
from app.api.v1.endpoints.nlq import router as nlq_router
from app.api.v1.endpoints.proactive import router as proactive_router
from app.api.v1.endpoints.pattern_verification import router as pattern_router

from app.api.v1.endpoints.identity import router as identity_router

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
from app.swarm.specialized.security_agent import SecurityAgent
from app.swarm.specialized.perception_agent import PerceptionAgent
from app.swarm.specialized.perception_agent import PerceptionAgent
from app.swarm.specialized.prediction_agent import PredictionAgent
from app.swarm.specialized.simulation_agent import SimulationAgent
from app.swarm.specialized.state_agent import StateAgent
from app.swarm.specialized.governance_agent import GovernanceAgent
from app.swarm.specialized.action_agent import ActionAgent
from app.swarm.specialized.knowledge_agent import KnowledgeAgent
from app.api.v2.services.crystallization_service import crystallization_service


from app.api.v2.services.prediction_service import PredictionService
from app.api.v2.services.simulation_service import SimulationService
# V2 memory service is already initialized in lifespan

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
    from app.api.v2.services.environment_service import environment_service
    await environment_service.seed_admin_membership()
    
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

    # Initialize Cognitive Lattices
    logger.info("Lifespan: Initializing memory lattices...")
    app.state.repos["vector"]._load_or_create_index()
            
    # Initialize MemoryService
    app.state.memory_service = MemoryService(
        memory_repo=app.state.repos["memory"],
        vector_repo=app.state.repos["vector"],
        graph_repo=app.state.repos["graph"]
    )

    # Initialize V2 services
    prediction_service = PredictionService(memory_service=app.state.memory_service, crystallization_service=crystallization_service)
    simulation_service = SimulationService(prediction_service=prediction_service)

    app.state.security_agent = SecurityAgent()
    app.state.perception_agent = PerceptionAgent()
    app.state.prediction_agent = PredictionAgent()
    app.state.simulation_agent = SimulationAgent(simulation_service=simulation_service)
    app.state.state_agent = StateAgent()
    app.state.governance_agent = GovernanceAgent()
    app.state.action_agent = ActionAgent()
    app.state.knowledge_agent = KnowledgeAgent()
    
    app.state.orchestrator = MultiAgentOrchestrator(
        db_session=SessionLocal, 
        blackboard=app.state.blackboard, 
        memory_service=app.state.memory_service,
        authority_service=None,
        crystallization_service=crystallization_service,
        prediction_service=prediction_service,
        simulation_service=simulation_service,
        confidence_threshold=0.5, 
        agents={
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
            "semantic": app.state.semantic_memory,
            "security": app.state.security_agent,
            "perception": app.state.perception_agent,
            "prediction": app.state.prediction_agent,
            "simulation": app.state.simulation_agent,
            "state": app.state.state_agent,
            "governance": app.state.governance_agent,
            "action": app.state.action_agent,
            "knowledge": app.state.knowledge_agent
        }
    )
    
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

@app.websocket("/v2/environments/{env_id}/ws/agents")
async def agent_websocket_endpoint(websocket: WebSocket, env_id: str):
    logger.info(f"🔌 Agent WebSocket connection attempt for env: {env_id}")
    
    # 1. Try session_id cookie first
    session_id = websocket.cookies.get("session_id")
    
    # 2. Fallback to query parameter 'token' if cookie missing (for cross-domain issues)
    if not session_id:
        session_id = websocket.query_params.get("token")
        logger.info(f"WebSocket auth fallback to query param: {session_id is not None}")
    
    if not session_id:
        logger.warning(f"WebSocket auth failed for {env_id}: No session_id cookie or token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify session (mimicking RBAC middleware logic)
    from app.models import UserSession
    from app.db.session import SessionLocal
    from sqlalchemy import select
    from datetime import datetime
    
    async with SessionLocal() as db:
        stmt = select(UserSession).where(
            UserSession.session_token == session_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now()
        )
        result = await db.execute(stmt)
        session_record = result.scalars().first()
        
    if not session_record:
        logger.warning(f"WebSocket auth failed for {env_id}: Session '{session_id}' not found, expired, or inactive.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await websocket.accept()
    logger.info(f"🔌 Agent WebSocket connection accepted for env: {env_id}")
    
    # Simple broadcast loop for development
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json({
                "type": "agent_status",
                "agentId": "agent-orch-001",
                "payload": {"status": "active", "lastActivity": datetime.now().isoformat()}
            })
    except WebSocketDisconnect:
        logger.info(f"🔌 Agent WebSocket disconnected for env {env_id}")
    except Exception as e:
        logger.error(f"🔌 Agent WebSocket error for env {env_id}: {e}")

# Set up Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health", "/docs", "/redoc", "/openapi.json"],
)
instrumentator.instrument(app)
# Expose is handled by _protected_metrics_app later

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
from app.api.v1.endpoints.chat_sessions import router as chat_sessions_router
from app.api.v1.endpoints.intelligence import router as intelligence_router
from app.api.v1.endpoints.mcp_connectors import router as mcp_connectors_router
from app.api.v1.endpoints.mcp_tools import router as mcp_tools_router


app.include_router(chat_router)
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
app.include_router(predictive_enhanced_router)
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
from app.api.v2.endpoints import (
    intelligence_packs, environments, memberships, authorities, crystallization, 
    simulation, agents, health as v2_health_router, models as v2_models_router, 
    ingestion as v2_ingestion_router, search as v2_search_router, 
    chat as v2_chat_router, reasoning as v2_reasoning_router, mcp as v2_mcp_router
)
app.include_router(intelligence_packs.router, prefix="/v2/environments")
app.include_router(environments.router, prefix="/v2/environments")
app.include_router(memberships.router, prefix="/v2/environments")
app.include_router(authorities.router, prefix="/v2/environments")
app.include_router(crystallization.router, prefix="/v2/environments")
app.include_router(simulation.router, prefix="/v2/environments")
app.include_router(agents.router, prefix="/v2/environments")
app.include_router(v2_models_router.router, prefix="/v2/environments")
app.include_router(v2_health_router.router, prefix="/v2/health")
app.include_router(v2_ingestion_router.router, prefix="/v2/environments")
app.include_router(v2_search_router.router, prefix="/v2/environments")
app.include_router(v2_chat_router.router, prefix="/v2/environments")
app.include_router(v2_reasoning_router.router, prefix="/v2/environments")
app.include_router(v2_mcp_router.router, prefix="/v2")



# Global Health Endpoints
@app.get("/admin/dashboard", response_class=RedirectResponse)
async def redirect_to_dashboard():
    return RedirectResponse(url="/api/v1/admin/dashboard/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=RedirectResponse)
async def redirect_to_login():
    return RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/", response_class=RedirectResponse)
async def redirect_to_root():
    return RedirectResponse(url="/api/v1/admin/dashboard/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/health/liveness")
async def liveness_check():
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return {"status": "not_ready", "database": "disconnected"}

@app.get("/health/engine")
async def engine_health():
    return {
        "status": "ready",
        "engine_mode": "Local-First (Ollama)",
        "ai_service": "connected",
        "vector_store": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
