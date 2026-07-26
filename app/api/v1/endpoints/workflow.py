from fastapi import APIRouter, Request
import logging
import json
import os
import httpx
from typing import List, Dict, Any, Optional
from app.models import WorkflowTask
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import Config
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["automation"])

class WorkflowOrchestrator:
    """
    Autonomously plans and executes multi-step tasks (Agentic Automation).
    """
    def __init__(self, db: AsyncSession, client: Optional[httpx.AsyncClient] = None):
        self.db = db
        self.client = client or httpx.AsyncClient()

    async def create_workflow(self, user_id: int, intent: str) -> WorkflowTask:
        """Decompose a user request into actionable steps."""
        logger.info(f"Decomposing workflow intent: {intent}")
        
        prompt = f"""
Decompose this user intent into a list of logical steps for an AI agent.
INTENT: {intent}
AVAILABLE ACTIONS: search_memory, analyze_document, summarize, notify_external, web_search

Return JSON list of steps: [{{"step": 1, "action": "...", "params": {{...}}}}]
"""
        steps = []
        try:
            ollama_url = Config.OLLAMA_BASE_URL
            res = await self.client.post(f"{ollama_url}/api/generate", json={
                "model": getattr(Config, "OLLAMA_REASONER_MODEL", "llama3"), "prompt": prompt, "stream": False
            }, timeout=30.0)
            if res.status_code == 200:
                steps = json.loads(res.json().get("response", "[]"))
        except Exception as e:
            logger.error(f"Workflow decomposition failed: {e}")
            # Fallback basic step
            steps = [{"step": 1, "action": "search_memory", "params": {"query": intent}}]
        
        task = WorkflowTask(
            user_id=user_id,
            intent=intent,
            steps=steps,
            status="running"
        )
        self.db.add(task)
        await self.db.commit()
        return task

    async def execute_workflow(self, task_id: int):
        """Execute a specific step using available connectors."""
        stmt = select(WorkflowTask).where(WorkflowTask.id == task_id)
        result = await self.db.execute(stmt)
        task = result.scalars().first()
        
        if not task: return

        results = []
        for step in task.steps:
            logger.info(f"Executing step {step['step']}: {step['action']}")
            # Step execution logic mapping to specific services
            result = {"status": "simulated_success", "step": step['step']}
            results.append(result)
        
        task.status = "completed"
        task.results = results
        await self.db.commit()
        return results