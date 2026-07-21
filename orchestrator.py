import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging
from app.schemas.memory_schemas import EpisodicEntry, MemoryResult, RetrievalPlan, EvaluationMetrics
from app.services.custom import PLASMA_ACTIVE

# Robust import for VeriLink Governance
logger = logging.getLogger(__name__)

try:
    from verilink_plugin import VeriLinkGovernancePlugin
    VERILINK_AVAILABLE = True
except ImportError:
    VeriLinkGovernancePlugin = None
    VERILINK_AVAILABLE = False

class ValidationRiskException(Exception):
    """Exception raised when the ValidatorAgent detects a high-risk assumption."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}

class MultiAgentOrchestrator:
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.active_tasks = 0
        self.agent_activity = {name: 0 for name in agents.keys()}
        self.recent_receipts = [] # For dashboard visualization
        self.offline_mode = False # Manual suppression flag
        self.constitution = self._load_constitution()
        
        # Initialize VeriLink Governance
        if VERILINK_AVAILABLE:
            try:
                self.governance = VeriLinkGovernancePlugin() # Removed unexpected 'config' argument
                logger.info("🛡️ VeriLink Governance Plugin initialized.")
            except Exception as e:
                logger.warning(f"⚠️ VeriLink Plugin loaded but service unreachable: {e}")
                self.governance = None
        
        self.governance_status = "active" if self.governance else "offline_fail_soft"
        
        # Ensure HITL service is available
        if "hitl" not in self.agents:
            raise ValueError("HITLService must be provided in agents dictionary.")

    def reload_constitution(self):
        """Reloads the local governance constitution from disk."""
        self.constitution = self._load_constitution()

    def _load_constitution(self) -> List[Dict]:
        """Loads local governance rules from a configuration file."""
        try:
            with open("governance_constitution.json", "r") as f:
                return json.load(f)
        except Exception:
            return []

    async def _local_guardian_policy_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal test logic passed to the VeriLink plugin for local enforcement."""
        intent = data.get("intent", "").lower()
        for rule in self.constitution:
            # Check for keyword violations if keywords are defined
            keywords = rule.get("keywords", [])
            if keywords and any(k in intent for k in keywords):
                return {
                    "passed": False, 
                    "block_reason": f"Policy Violation: {rule['rule']}",
                    "rule_id": rule['id']
                }
        return {"passed": True, "status": "verified_locally"}

    async def _run_agent(self, agent_name: str, method_name: str, *args, **kwargs):
        """Helper to run an agent method while tracking its activity."""
        if agent_name not in self.agent_activity:
            self.agent_activity[agent_name] = 0
            
        self.agent_activity[agent_name] += 1
        try:
            agent = self.agents.get(agent_name)
            if not agent:
                # Log a warning if an agent is missing but don't fail unless critical
                # For now, let's assume missing agents are critical for the flow
                raise ValueError(f"Agent '{agent_name}' not found in orchestrator.")
            method = getattr(agent, method_name)
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            return method(*args, **kwargs)
        finally:
            self.agent_activity[agent_name] -= 1
    
    async def process(self, query: str, context: Dict[str, Any] = None, sensitivity: str = "medium", risk_threshold: float = 0.8):
        self.active_tasks += 1
        user_id = context.get("user_id", 0) if context else 0
        
        logger.info(f"🧠 Cognitive Pipeline Ignited: '{query[:50]}...' (Sensitivity: {sensitivity})")

        # Initialize response variables for safety during evaluation/logging
        response_text = ""
        retrieval_data: List[MemoryResult] = []
        generation = {}
        plan: Optional[RetrievalPlan] = None
        reasoning_insight: str = ""
        response_tone: str = "neutral"
        route: Dict[str, Any] = {}
        evaluation: Optional[EvaluationMetrics] = None
        gov_receipt_id: Optional[str] = None
        gov_status: str = "skipped"
        signature: Optional[str] = None

        # 1. Strategic Planning
        plan = await self._run_agent("planner", "create_plan", query, context=context)
        logger.info(f"📋 Strategic Plan created. Complexity: {plan.complexity_score}")

        # Tag Plasma state based on high-complexity reasoning requirement (> 0.7)
        is_plasma = plan.complexity_score > 0.7
        if is_plasma:
            PLASMA_ACTIVE.inc()
        
        # Determine response tone based on situational awareness (Layer 1)
        situational_data = context.get("situational_awareness", {}) if context else {}
        response_tone = await self._run_agent("empathy", "determine_tone", situational_awareness=situational_data)
        logger.info(f"🎭 Empathy Agent set tone to: {response_tone}")

        try:
            # 2. Parallel Execution (Retrieval + Reasoning)
            tasks = []
            logger.info("⚙️ Executing Retrieval and Reasoning in parallel...")
            if self.agents.get("retriever"):
                tasks.append(self._run_agent("retriever", "hybrid_search", plan, user_id))
            else:
                tasks.append(asyncio.sleep(0, result=[]))

            if self.agents.get("reasoner"):
                tasks.append(self._run_agent("reasoner", "analyze", query, context=context))
            else:
                tasks.append(asyncio.sleep(0, result="Reasoning agent not yet initialized."))

            results = await asyncio.gather(*tasks)
            retrieval_data, reasoning_insight = results
            logger.info(f"🔍 Retrieval complete ({len(retrieval_data)} results). Reasoning insight generated.")
            
            # 2.1 Pre-Governance Intent Check (Offline-Ready)
            if self.governance and not self.offline_mode:
                # We wrap the reasoning in a 'test' to see if it violates core ethics
                # even if the server is offline, this prepares the VAP receipt structure
                try:
                    gov_check = await self.governance.run_test(
                        {
                            "intent": reasoning_insight,
                            "agent_id": "personavault_core",
                            "complexity": plan.complexity_score
                        },
                        self._local_guardian_policy_check
                    )
                    
                    gov_receipt_id = getattr(gov_check, "receipt_id", "local_pending")
                    signature = getattr(gov_check, "signature", "local_seal_v1")
                    gov_status = "verified" if gov_check.passed else "blocked"
                    
                    # IMMEDIATE VALUE: Stop the AI if local governance fails
                    if not gov_check.passed:
                        logger.error(f"🚫 BLOCKED BY GUARDIAN: {gov_receipt_id}")
                        return {
                            "answer": "I am sorry, but system governance policies have flagged this reasoning path as unsafe.",
                            "confidence": 0.0,
                            "governance_receipt": gov_receipt_id,
                            "status": "BLOCKED_BY_GUARDIAN",
                            "trace": {"reasoning": reasoning_insight}
                        }

                    # Record receipt for dashboard visualization
                    self.recent_receipts.append({
                        "id": gov_receipt_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "VERIFIED" if gov_check.passed else "BLOCKED"
                    })
                    if len(self.recent_receipts) > 15: self.recent_receipts.pop(0)
                except Exception:
                    logger.debug("VeriLink kernel unreachable - proceeding with local fail-soft.")
                    gov_status = "offline_bypass" # Fail-soft if VeriLinkOS is unreachable

            # 3. Validation
            is_valid = True
            validation_res = {}
            if self.agents.get("validator"):
                logger.info("⚖️ Validator Agent assessing reasoning risk...")
                try:
                    validation_res = await self._run_agent("validator", "validate",
                        query=query, 
                        evidence=retrieval_data, 
                        logic=reasoning_insight
                    )
                    
                    is_valid = validation_res.get("is_valid", True)
                    risk_score = validation_res.get("risk_score", 0.0)

                    if risk_score >= risk_threshold or not is_valid:
                        logger.warning(f"⚠️ High Risk Detected ({risk_score}). Escalating to HITL.")
                        # Trigger HITL for validation risk
                        orchestrator_state = {
                            "query": query,
                            "context": context,
                            "plan": plan.dict(),
                            "retrieval_data": [r.dict() for r in retrieval_data],
                            "reasoning_insight": reasoning_insight,
                            "response_tone": response_tone,
                            "situational_data": situational_data,
                            "route": {}, # Route is determined later, so it's empty here
                            "evaluation": None, # Evaluation is determined later
                            "interruption_point": "validation_risk",
                            "validation_details": validation_res
                        }
                        pending_action = await self._run_agent("hitl", "request_clarification",
                            agent_type="ValidatorAgent",
                            query=f"Validation failed for query: '{query}'. Reason: {validation_res.get('explanation')}",
                            options=orchestrator_state,
                            vap_hash=gov_receipt_id, # Link cryptographic receipt to HITL record
                            action_chain_id=signature  # Link to the VeriLink Action Chain
                        )
                        return {
                            "status": "HITL_REQUIRED",
                            "pending_action_id": pending_action["id"],
                        }
                except Exception:
                    # Fallback to ensure logic continues if validator fails
                    pass
            
            # 4. Intelligent Routing
            logger.info("🚦 Routing query to optimal AI Tier...")
            route = await self._run_agent("router", "get_route",
                query=query, 
                complexity=plan.complexity_score, 
                sensitivity=sensitivity
            )

            # 5. Final Synthesis
            logger.info(f"✍️ Synthesizing response via {route.get('provider', 'default')}...")
            generation = await self._run_agent("generator", "generate",
                query, 
                retrieval_data, 
                reasoning_insight, 
                route=route, 
                response_tone=response_tone,
                situational_awareness=situational_data
            )
            response_text = generation.get("answer", "")
        finally:
            if is_plasma:
                PLASMA_ACTIVE.dec()
            self.active_tasks -= 1

        # 6. Quality Evaluation (Judge)
        evaluation = None
        if self.agents.get("judge"):
            logger.info("👨‍⚖️ Judge Agent performing quality audit...")
            evaluation = await self._run_agent("judge", "evaluate", query, response_text, retrieval_data)

        # 7. Log to Episodic Memory (Layer 2)
        if self.agents.get("episodic"):
            logger.info("💾 Archiving interaction to Layer 2 (Episodic)...")
            entry = EpisodicEntry(
                query=query,
                plan=plan.dict() if hasattr(plan, 'dict') else plan,
                results=[r.dict() if hasattr(r, 'dict') else r for r in retrieval_data],
                answer=response_text,
                evaluation=evaluation.dict() if hasattr(evaluation, 'dict') else evaluation,
                governance_receipt_id=gov_receipt_id or f"offline_{datetime.utcnow().strftime('%Y%m%d')}",
                signature=signature,
                hitl_approved=False,
                timestamp=datetime.utcnow()
            )
            await self._run_agent("episodic", "store", entry)

        return {
            "answer": response_text,
            "evaluation": evaluation.dict() if evaluation else None,
            "source": generation.get("source"),
            "confidence": generation.get("confidence", 0.0),
            "hitl_approved": False,
            "thermodynamic_state": "plasma" if is_plasma else "stable",
            "governance_receipt": gov_receipt_id or "offline_mode",
            "trace": {
                "plan": plan.dict(),
                "retrieval": [r.dict() for r in retrieval_data],
                "reasoning": reasoning_insight,
                "empathy": response_tone,
                "governance_status": gov_status,
                "governance_receipt": gov_receipt_id,
                "signature": signature
            }
        }

    async def override_validation(
        self, 
        query: str, 
        retrieval_data: List[MemoryResult], 
        reasoning_insight: str, 
        context: Dict[str, Any] = None,
        sensitivity: str = "medium"
    ):
        self.active_tasks += 1
        """Proceeds with generation by bypassing the ValidatorAgent, typically used for HITL approvals."""
        
        # 1. Re-generate the plan to get metadata (needed for accurate Layer 3 logging)
        # Determine response tone based on situational awareness (Layer 1)
        situational_data = context.get("situational_awareness", {}) if context else {}
        response_tone = await self._run_agent("empathy", "determine_tone", situational_awareness=situational_data)

        plan = await self._run_agent("planner", "create_plan", query, context=context)
        
        is_plasma = plan.complexity_score > 0.7
        if is_plasma:
            PLASMA_ACTIVE.inc()

        # 2. Re-calculate routing based on the query complexity
        route = await self._run_agent("router", "get_route",
            query=query, 
            complexity=plan.complexity_score, 
            sensitivity=sensitivity
        )

        try:
            # 3. Final Synthesis (Bypassing step 3: Validation)
            generation = await self._run_agent("generator", "generate",
                query, 
                retrieval_data, 
                reasoning_insight, 
                route=route, 
                hitl_approved=True, 
                response_tone=response_tone,
                situational_awareness=situational_data
            )
            response_text = generation.get("answer", "")
        finally:
            if is_plasma:
                PLASMA_ACTIVE.dec()
            self.active_tasks -= 1

        # 4. Quality Evaluation (Judge)
        evaluation = None
        if self.agents.get("judge"):
            evaluation = await self._run_agent("judge", "evaluate", query, response_text, retrieval_data)

        # 5. Log to Episodic Memory (Layer 2)
        if self.agents.get("episodic"):
            entry = EpisodicEntry(
                query=query,
                plan=plan.dict() if hasattr(plan, 'dict') else plan,
                results=[r.dict() if hasattr(r, 'dict') else r for r in retrieval_data],
                answer=response_text,
                evaluation=evaluation.dict() if hasattr(evaluation, 'dict') else evaluation,
                hitl_approved=True,
                governance_receipt_id=self.recent_receipts[-1]["id"] if self.recent_receipts else "local_override",
                timestamp=datetime.utcnow()
            )
            await self._run_agent("episodic", "store", entry)

        return {
            "answer": response_text,
            "evaluation": evaluation.dict() if evaluation else None,
            "source": generation.get("source"),
            "confidence": generation.get("confidence", 0.0),
            "hitl_approved": generation.get("hitl_approved", False),
            "thermodynamic_state": "plasma" if is_plasma else "stable",
            "trace": {
                "plan": plan.dict(),
                "retrieval": [r.dict() for r in retrieval_data],
                "reasoning": reasoning_insight,
                "empathy": response_tone,
                "governance_receipt": self.recent_receipts[-1]["id"] if self.recent_receipts else None
            }
        }