#!/usr/bin/env python3
"""
Test script for the PersonaVault swarm orchestration.
Bypasses Neo4j for Cloud Shell compatibility.
"""

import asyncio
import sys
import types
sys.path.insert(0, '.')

# ============ MOCK GRAPH SERVICE ============
# Create a mock graph service that doesn't require Neo4j
class MockGraphService:
    def __init__(self):
        self.driver = None
    def create_memory_node(self, *args, **kwargs):
        pass
    def create_relationship(self, *args, **kwargs):
        pass
    def execute_query(self, query):
        return []
    def check_health(self):
        return False
    def close(self):
        pass

# Patch the graph_service module BEFORE importing
import app.services.graph_service
app.services.graph_service.GraphDatabase = None
app.services.graph_service.graph_service = MockGraphService()
app.services.graph_service.GraphService = MockGraphService

# Now import the rest
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.db.session import SessionLocal
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
from app.services.episodic_memory import EpisodicMemory
from app.services.semantic_memory import SemanticMemory
from app.services.vector_service import vector_service
from app.services.blackboard import CognitiveBlackboard

async def test_swarm():
    logger.info("🧠 Starting swarm test...")
    
    async with SessionLocal() as db:
        # Create memory services
        semantic_memory = SemanticMemory(db)
        episodic_memory = EpisodicMemory(db)
        
        # Use mock graph service
        mock_graph = MockGraphService()
        
        # Create agents
        agents = {
            "planner": PlannerAgent(semantic_memory),
            "retriever": RetrievalAgent(vector_service, mock_graph),
            "generator": GeneratorAgent(),
            "judge": JudgeAgent(),
            "router": AIRouter("Local-First (Ollama)"),
            "reasoner": ReasonerAgent(),
            "validator": ValidatorAgent(),
            "empathy": EmpathyAgent(),
            "hitl": HITLService(SessionLocal),
            "episodic": episodic_memory,
            "semantic": semantic_memory
        }
        
        # Create orchestrator with blackboard
        blackboard = CognitiveBlackboard()
        orchestrator = MultiAgentOrchestrator(db, agents)
        
        # Run a query
        logger.info("📝 Processing query: 'What is the purpose of PersonaVault?'")
        
        result = await orchestrator.run(
            query="What is the purpose of PersonaVault?",
            context={"user_id": 1}
        )
        
        print("\n" + "="*60)
        print("📊 SWARM RESPONSE")
        print("="*60)
        print(f"✅ Answer:\n{result.get('answer', 'No answer')[:500]}")
        print(f"\n📊 Confidence: {result.get('confidence', 0)}")
        
        eval_data = result.get('evaluation', {})
        if eval_data:
            print(f"📈 Evaluation:")
            print(f"   Passed: {eval_data.get('passed', False)}")
            print(f"   Faithfulness: {eval_data.get('faithfulness', 0)}")
            print(f"   Confidence: {eval_data.get('confidence', 0)}")
        
        print("="*60)
        return result

if __name__ == "__main__":
    result = asyncio.run(test_swarm())
    print("\n✅ Swarm test complete!")
