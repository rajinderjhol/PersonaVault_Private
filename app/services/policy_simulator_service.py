import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.simulation import SimulationJob
from app.models.decision_trace import DecisionTrace

logger = logging.getLogger(__name__)

class PolicySimulatorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_attestation(self, results: Dict, params: Dict) -> str:
        """Generate attestation for simulation result."""
        data_to_sign = f"{json.dumps(results)}{json.dumps(params)}{datetime.utcnow().isoformat()}"
        return f"vap:sha256:{hashlib.sha256(data_to_sign.encode()).hexdigest()[:32]}"

    async def simulate_policy_impact(
        self,
        domain: str,
        params: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        # 1. Fetch historical decisions
        stmt = select(DecisionTrace).where(
            DecisionTrace.pack_name == domain,
            DecisionTrace.timestamp.between(start_date, end_date)
        )
        traces = (await self.db.execute(stmt)).scalars().all()
        
        if not traces:
            return {"error": "No historical data found for the given domain and time range."}
        
        # 2. Simulate logic
        simulated_results = []
        for trace in traces:
            # Apply policy adjustment (example logic)
            simulated_confidence = (trace.confidence_score or 0.5) * params.get("confidence_multiplier", 1.0)
            simulated_results.append({
                "original_confidence": trace.confidence_score or 0.5,
                "simulated_confidence": min(simulated_confidence, 1.0)
            })
        
        # 3. Aggregate
        avg_original = sum(r["original_confidence"] for r in simulated_results) / len(simulated_results)
        avg_simulated = sum(r["simulated_confidence"] for r in simulated_results) / len(simulated_results)
        
        metrics = {
            "avg_original_confidence": avg_original,
            "avg_simulated_confidence": avg_simulated,
            "impact": avg_simulated - avg_original
        }
        
        # 4. Generate Attestation
        attestation = self._generate_attestation(metrics, params)
        
        # 5. Save Job
        job = SimulationJob(
            job_id=f"sim_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}",
            domain=domain,
            params=params,
            status="completed",
            result_metrics=metrics,
            attestation=attestation,
            completed_at=datetime.utcnow()
        )
        self.db.add(job)
        await self.db.commit()
        
        return {"job_id": job.job_id, "metrics": metrics, "attestation": attestation}
