import logging
import asyncio
import httpx
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select, inspect
from datetime import datetime

from app.config import Config
from app.db.session import engine, Base, SessionLocal
from app.models import User, Organization, SystemConfig, UserSession, Memory, AuditLog
from app.services.task_service import init_scheduler, scheduler
from app.services.graph_service import graph_service
from app.services.vector_service import vector_service
from app.services.memory_service import MemoryService
from app.services.semantic_memory import SemanticMemory
from app.services.episodic_memory import EpisodicMemory
from app.services.planning_agent import PlanningAgent
from app.services.retrieval_agent import RetrievalAgent
from app.services.generator_agent import GeneratorAgent
from app.services.judge_agent import JudgeAgent
from app.services.reasoner_agent import ReasonerAgent
from app.services.empathy_agent import EmpathyAgent
from app.services.validator_agent import ValidatorAgent
from app.services.ai_router import AIRouter
from app.services.hitl_service import HITLService
from app.services.approval import ApprovalService
from app.adapters.medical_adapter import MedicalTelemetryAdapter
from app.services.mcp_server import MCPServer
from orchestrator import MultiAgentOrchestrator
from app.services.consolidation_service import ConsolidationTask

logger = logging.getLogger(__name__)

async def ensure_ollama_models(app: FastAPI):
    """Ensures all required models in Config are pulled and ready."""
    client = app.state.ai_client
    if Config.IS_AIR_GAPPED:
        logger.info("Lifespan: Air-gapped mode active. Skipping automated model pulls.")
        return

    required_models = {
        Config.OLLAMA_LLM_MODEL,
        Config.OLLAMA_JUDGE_MODEL,
        Config.OLLAMA_REASONER_MODEL,
        Config.OLLAMA_EMBEDDING_MODEL
    }

    try:
        tags_res = await client.get(f"{Config.OLLAMA_BASE_URL}/api/tags")
        installed_models = [m["name"] for m in tags_res.json().get("models", [])]
        
        for model in required_models:
            if model not in installed_models and f"{model}:latest" not in installed_models:
                app.state.is_pulling_models = True
                logger.info(f"Lifespan: Required model '{model}' missing. Initiating pull...")
                await client.post(f"{Config.OLLAMA_BASE_URL}/api/pull", json={"name": model}, timeout=None)
                logger.info(f"✅ Lifespan: Model '{model}' pulled successfully.")
        app.state.is_pulling_models = False
    except Exception as e:
        logger.warning(f"Lifespan: Could not verify/pull Ollama models: {e}")
        app.state.is_pulling_models = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize background scheduler
    init_scheduler()

    logger.info("Lifespan: Synchronizing database lattices...")
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
        
        def check_integrity(sync_conn):
            inspector = inspect(sync_conn)
            existing_tables = inspector.get_table_names()
            target_tables = ["memories", "episodic_entries"]
            for table in target_tables:
                if table in existing_tables:
                    columns = [col["name"] for col in inspector.get_columns(table)]
                    status = "✅" if "query" in columns else "❌"
                    logger.info(f"{status} Lattice Integrity: Table '{table}' | query_column: {'present' if 'query' in columns else 'MISSING'}")
        await conn.run_sync(check_integrity)

    # 1.1 Preseed admin account
    async with SessionLocal() as db:
        try:
            admin_exists = (await db.execute(select(User).where(User.username == "admin"))).scalars().first()
            if not admin_exists:
                org = (await db.execute(select(Organization).where(Organization.slug == "default"))).scalars().first()
                if not org:
                    org = Organization(name="Default Org", slug="default")
                    db.add(org); await db.flush()
                db.add(User(username="admin", email="admin@personavault.local", hashed_password="admin123", role="admin", organization_id=org.id))
                await db.commit()
                logger.info("Lifespan: Admin account seeded successfully.")
        except Exception as e:
            logger.error(f"Lifespan: Seeding failed: {e}"); await db.rollback()

    # 2. Initialize Infrastructure
    app.state.ai_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0), limits=httpx.Limits(max_keepalive_connections=10, max_connections=20))
    app.state.graph_service = graph_service
    app.state.vector_service = vector_service
    app.state.vector_service._client = app.state.ai_client
    app.state.is_pulling_models = False
    
    try:
        ai_check = await app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=1.0)
        app.state.ai_engine_mode = "Local-First (Ollama)" if ai_check.status_code == 200 else "Hybrid (Cloud Fallback)"
    except Exception:
        app.state.ai_engine_mode = "Hybrid (Cloud Fallback)"
    
    if "Ollama" in app.state.ai_engine_mode:
        asyncio.create_task(ensure_ollama_models(app))

    # 3. Initialize Cognitive Swarm
    app.state.ai_router = AIRouter(engine_mode=app.state.ai_engine_mode)
    app.state.semantic_memory = SemanticMemory(SessionLocal)
    app.state.planning_agent = PlanningAgent(semantic_memory=app.state.semantic_memory)
    app.state.retrieval_agent = RetrievalAgent(vector_store=app.state.vector_service, graph_service=app.state.graph_service)
    app.state.generator_agent = GeneratorAgent(client=app.state.ai_client)
    app.state.judge_agent = JudgeAgent(ollama_url=Config.OLLAMA_BASE_URL, client=app.state.ai_client)
    app.state.empathy_agent = EmpathyAgent(ollama_url=Config.OLLAMA_BASE_URL, client=app.state.ai_client, session_factory=SessionLocal)
    app.state.reasoner_agent = ReasonerAgent(client=app.state.ai_client)
    app.state.validator_agent = ValidatorAgent(client=app.state.ai_client)
    app.state.episodic_memory = EpisodicMemory(SessionLocal)
    app.state.approval_service = ApprovalService(SessionLocal)
    app.state.hitl_service = HITLService(SessionLocal)

    agents = {
        "planner": app.state.planning_agent, "retriever": app.state.retrieval_agent, "reasoner": app.state.reasoner_agent,
        "validator": app.state.validator_agent, "hitl": app.state.hitl_service, "generator": app.state.generator_agent,
        "judge": app.state.judge_agent, "router": app.state.ai_router, "episodic": app.state.episodic_memory,
        "empathy": app.state.empathy_agent, "approval": app.state.approval_service
    }
    app.state.orchestrator = MultiAgentOrchestrator(agents=agents)

    # 4. Initialize Physics & Maintenance
    app.state.memory_service = MemoryService(db=SessionLocal, vector_service=app.state.vector_service, graph_service=app.state.graph_service)
    app.state.medical_adapter = MedicalTelemetryAdapter(orchestrator=app.state.orchestrator)
    app.state.mcp_server = MCPServer(memory_service=app.state.memory_service)

    consolidation_config = {"batch_size": 10, "interval_hours": 1.0}
    async with SessionLocal() as db:
        try:
            configs_res = await db.execute(select(SystemConfig).where(SystemConfig.key.in_(["graduation_batch_size", "graduation_interval", "last_empathy_mood", "last_empathy_tone"])))
            for cfg in configs_res.scalars().all():
                if cfg.key == "graduation_batch_size": consolidation_config["batch_size"] = int(cfg.value)
                elif cfg.key == "graduation_interval": consolidation_config["interval_hours"] = float(cfg.value)
                elif cfg.key == "last_empathy_mood": app.state.empathy_agent.last_mood = cfg.value
                elif cfg.key == "last_empathy_tone": app.state.empathy_agent.last_tone = cfg.value
        except Exception: pass
    
    app.state.consolidation_task = ConsolidationTask(orchestrator=app.state.orchestrator, memory_service=app.state.memory_service, config=consolidation_config)
    app.state.consolidation_task.batch_size = consolidation_config["batch_size"]
    app.state.consolidation_task.interval_hours = consolidation_config["interval_hours"]
    app.state.consolidation_task.trigger_event = asyncio.Event()
    asyncio.create_task(app.state.consolidation_task.run())

    # --- Status Summary ---
    logger.info(f"✨ PersonaVault AI Core Services Online")
    logger.info(f"➜ AI Mode:     {app.state.ai_engine_mode}")
    logger.info(f"➜ Infra Mode:  {Config.INFRA_MODE}")
    logger.info(f"➜ Admin Dash:  http://localhost:8000/admin/dashboard")

    yield
    # Graceful shutdown
    scheduler.shutdown(wait=False)
    if hasattr(app.state, 'ai_client'): await app.state.ai_client.aclose()
    if hasattr(app.state, 'graph_service'): app.state.graph_service.close()
    logger.info("Lifespan: All services shut down gracefully.")