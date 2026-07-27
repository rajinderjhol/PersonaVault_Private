#!/usr/bin/env python3
"""
Test script for the PersonaVault swarm orchestration.
Uses mock Neo4j module for Cloud Shell compatibility.
"""

import sys
import os
import httpx

# Add mock modules to path BEFORE importing app
sys.path.insert(0, os.path.join(os.getcwd(), 'mock_modules'))

# Now import neo4j - it will use our mock
import neo4j
print("✅ Using mock Neo4j module")

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import app modules
sys.path.insert(0, os.getcwd())

from app.db.session import SessionLocal
from app.services.vector_service import vector_service
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.services.blackboard import CognitiveBlackboard
from app.swarm.core.planner import PlannerAgent
from app.swarm.core.retriever import RetrievalAgent
from app.swarm.core.generator import GeneratorAgent
from app.swarm.core.judge import JudgeAgent
from app.swarm.core.reasoner import ReasonerAgent
from app.swarm.core.validator import ValidatorAgent
from app.swarm.core.router import AIRouter
from app.swarm.interaction.empathy import EmpathyAgent
from app.swarm.interaction.hitl import HITLService
from app.swarm.orchestrator import MultiAgentOrchestrator
from app.services.awareness_service import AwarenessService

# Mock graph service
from app.services.graph_service import graph_service

# Mock PersonaProfiler
class MockPersonaProfiler:
    def __init__(self, db):
        self.db = db
    
    async def get_or_create_profile(self, user_id):
        class MockProfile:
            writing_style = "balanced"
            communication_style = "casual"
        return MockProfile()

# Patch the persona profiler
import app.api.v1.endpoints.persona
app.api.v1.endpoints.persona.PersonaProfiler = MockPersonaProfiler

logger.info("🧠 Starting swarm test with mock Neo4j...")

# Create a proper session factory
class SessionFactory:
    def __call__(self):
        return SessionLocal()

async def test_swarm():
    # Initialize HTTP client for vector service
    logger.info("📡 Initializing HTTP client...")
    vector_service._client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    
    # Load vector index
    logger.info("📊 Loading vector index...")
    vector_service._load_or_create_index()
    logger.info(f"📊 Vector index loaded with {len(vector_service.metadata)} entries")
    
    # Create session factory
    session_factory = SessionFactory()
    
    # Create memory services with a session
    async with SessionLocal() as db:
        semantic_memory = SemanticMemory(db)
        episodic_memory = EpisodicMemory(db)
        
        logger.info("📝 Creating agents...")
        
        # Create agents
        agents = {
            "planner": PlannerAgent(semantic_memory),
            "retriever": RetrievalAgent(vector_service, graph_service),
            "generator": GeneratorAgent(),
            "judge": JudgeAgent(),
            "router": AIRouter("Local-First (Ollama)"),
            "reasoner": ReasonerAgent(),
            "validator": ValidatorAgent(),
            "empathy": EmpathyAgent(),
            "hitl": HITLService(session_factory),
            "episodic": episodic_memory,
            "semantic": semantic_memory
        }
        
        # Create orchestrator with session factory
        orchestrator = MultiAgentOrchestrator(session_factory, agents)
        
        # Override persona profiler with mock that uses session
        from app.api.v1.endpoints.persona import PersonaProfiler
        orchestrator.persona_profiler = PersonaProfiler(db)
        
        # Run a query
        logger.info("📝 Processing query: 'What is the purpose of PersonaVault?'")
        
        result = await orchestrator.run(
            query="What is the purpose of PersonaVault?",
            context={"user_id": 1}
        )
        
        print("\n" + "="*60)
        print("📊 SWARM RESPONSE")
        print("="*60)
        
        answer = result.get('answer', 'No answer')
        if len(answer) > 300:
            answer = answer[:300] + "..."
        print(f"✅ Answer:\n{answer}")
        
        print(f"\n📊 Confidence: {result.get('confidence', 0)}")
        
        eval_data = result.get('evaluation', {})
        if eval_data:
            print(f"📈 Evaluation:")
            print(f"   Passed: {eval_data.get('passed', False)}")
            print(f"   Faithfulness: {eval_data.get('faithfulness', 0)}")
            print(f"   Confidence: {eval_data.get('confidence', 0)}")
        
        print("="*60)
        
        # Clean up
        await vector_service._client.aclose()
        return result

if __name__ == "__main__":
    result = asyncio.run(test_swarm())
    print("\n✅ Swarm test complete!")
