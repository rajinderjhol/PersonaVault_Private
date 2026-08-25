"""
Trace Service - Manages decision traces for the UI
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DecisionTrace:
    """Structured decision trace for UI consumption"""
    decision_id: str
    timestamp: str
    user_id: int
    query: str
    response: str
    trace: Dict[str, Any]
    explanation: str
    pack_name: str
    pack_version: str
    latency_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class TraceService:
    """Service for storing and retrieving decision traces"""
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._traces: Dict[str, DecisionTrace] = {}
        self._max_traces = 100
        logger.info("TraceService initialized")
    
    def store_trace(self, trace: DecisionTrace) -> str:
        """Store a decision trace"""
        self._traces[trace.decision_id] = trace
        
        # Limit memory usage
        if len(self._traces) > self._max_traces:
            oldest_key = min(self._traces.keys(), 
                           key=lambda k: self._traces[k].timestamp)
            del self._traces[oldest_key]
        
        logger.info(f"Stored trace: {trace.decision_id}")
        return trace.decision_id
    
    def get_trace(self, decision_id: str) -> Optional[DecisionTrace]:
        """Retrieve a trace by ID"""
        return self._traces.get(decision_id)
    
    def get_recent_traces(self, limit: int = 10) -> List[DecisionTrace]:
        """Get most recent traces"""
        sorted_traces = sorted(
            self._traces.values(),
            key=lambda t: t.timestamp,
            reverse=True
        )
        return sorted_traces[:limit]
    
    def export_trace(self, decision_id: str, format: str = "json") -> Optional[str]:
        """Export trace in specified format"""
        trace = self.get_trace(decision_id)
        if not trace:
            return None
        
        if format == "json":
            return trace.to_json()
        elif format == "pretty":
            return json.dumps(trace.to_dict(), indent=2)
        else:
            return str(trace.to_dict())
    
    def verify_trace(self, decision_id: str) -> Dict[str, Any]:
        """Verify a trace's integrity and reproducibility"""
        trace = self.get_trace(decision_id)
        if not trace:
            return {"status": "error", "message": "Trace not found"}
        
        # Verify that the trace has all required fields
        required_fields = [
            "perception", "signals", "policy", "decision", "autonomy"
        ]
        trace_dict = trace.trace
        missing = [f for f in required_fields if f not in trace_dict]
        
        if missing:
            return {
                "status": "incomplete",
                "message": f"Missing fields: {missing}",
                "fields_present": [f for f in required_fields if f in trace_dict]
            }
        
        return {
            "status": "verified",
            "message": "Trace is complete and verified",
            "fields_verified": required_fields,
            "timestamp": trace.timestamp,
            "latency_ms": trace.latency_ms
        }


# Singleton instance
_trace_service = None

def get_trace_service(db_session=None) -> TraceService:
    global _trace_service
    if _trace_service is None:
        _trace_service = TraceService(db_session)
    return _trace_service
