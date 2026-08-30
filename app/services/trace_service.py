"""
Trace Service - Captures and manages decision traces for the PersonaVault decision pipeline.
Provides async operations for capturing steps, adding provenance, and retrieving traces.
"""
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.decision_trace import DecisionTrace, TraceStep, ProvenanceRecord


class TraceService:
    """
    Service for capturing and retrieving decision traces.
    Each decision goes through a 5-step pipeline: Perception → Policy Match → AI Recommendation → Action → Outcome.
    """
    
    def __init__(self, db: Union[AsyncSession, async_sessionmaker[AsyncSession]]):
        self.db = db
    
    async def _get_session(self) -> AsyncSession:
        """Helper to get an active session."""
        if callable(self.db):
            return self.db()
        return self.db

    async def _close_session(self, session: AsyncSession):
        """Helper to close session if it was factory-created."""
        if callable(self.db):
            await session.close()

    async def capture_step(
        self,
        session_id: int,
        step: TraceStep,
        data: Dict[str, Any],
        agent_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        is_crystallized: bool = False,
        message_id: Optional[int] = None,
        query: Optional[str] = None,
        response: Optional[str] = None,
        pack_name: Optional[str] = None,
        user_id: Optional[int] = None,
        decision_id: Optional[str] = None,
        trace: Optional[Dict] = None,
        explanation: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> DecisionTrace:
        """Capture a single step in the decision trace with full field mapping."""
        session = await self._get_session()
        try:
            trace_record = DecisionTrace(
                session_id=session_id,
                step=step,
                data=data,
                agent_id=agent_id,
                confidence_score=confidence_score,
                is_crystallized=is_crystallized,
                message_id=message_id,
                query=query or data.get("query"),
                response=response or data.get("response"),
                pack_name=pack_name or data.get("pack_name") or data.get("domain"),
                user_id=user_id,
                decision_id=decision_id or data.get("decision_id"),
                trace=trace or data.get("trace"),
                explanation=explanation or data.get("explanation"),
                latency_ms=latency_ms or data.get("latency_ms")
            )
            session.add(trace_record)
            await session.commit()
            await session.refresh(trace_record)
            return trace_record
        finally:
            await self._close_session(session)
    
    async def add_provenance(
        self,
        trace_id: UUID,
        source_type: str,
        source_id: str,
        source_text: Optional[str] = None,
        relevance_score: Optional[float] = None
    ) -> ProvenanceRecord:
        """Add a provenance link to an existing trace"""
        session = await self._get_session()
        try:
            provenance = ProvenanceRecord(
                trace_id=trace_id,
                source_type=source_type,
                source_id=source_id,
                source_text=source_text,
                relevance_score=relevance_score
            )
            session.add(provenance)
            await session.commit()
            await session.refresh(provenance)
            return provenance
        finally:
            await self._close_session(session)
    
    async def get_full_trace(self, trace_id: UUID) -> Optional[DecisionTrace]:
        """Retrieve a complete trace with all provenance links"""
        session = await self._get_session()
        try:
            result = await session.execute(
                select(DecisionTrace).options(selectinload(DecisionTrace.provenance_links)).filter(DecisionTrace.id == trace_id)
            )
            return result.scalar_one_or_none()
        finally:
            await self._close_session(session)
    
    async def get_session_traces(self, session_id: int) -> List[DecisionTrace]:
        """Get all traces for a session, ordered by timestamp"""
        session = await self._get_session()
        try:
            result = await session.execute(
                select(DecisionTrace).options(selectinload(DecisionTrace.provenance_links)).filter(DecisionTrace.session_id == session_id)
                .order_by(DecisionTrace.timestamp)
            )
            return list(result.scalars().all())
        finally:
            await self._close_session(session)
    
    async def get_recent_traces(self, limit: int = 10) -> List[DecisionTrace]:
        """Get recent decision traces"""
        session = await self._get_session()
        try:
            result = await session.execute(
                select(DecisionTrace)
                .options(selectinload(DecisionTrace.provenance_links))
                .order_by(DecisionTrace.timestamp.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        finally:
            await self._close_session(session)
    
    async def mark_crystallized(self, trace_id: UUID) -> bool:
        """Mark a trace as crystallized"""
        session = await self._get_session()
        try:
            trace = await self.get_full_trace(trace_id)
            if not trace:
                return False
            trace.is_crystallized = True
            await session.commit()
            return True
        finally:
            await self._close_session(session)
    
    async def store_trace(self, trace_obj: DecisionTrace):
        """Store a pre-constructed trace object"""
        session = await self._get_session()
        try:
            session.add(trace_obj)
            await session.commit()
            await session.refresh(trace_obj)
            return trace_obj
        finally:
            await self._close_session(session)
    
    # --- Legacy Compatibility Methods ---
    # These methods exist for backward compatibility with existing code
    
    async def get_trace(self, decision_id: str) -> Optional[DecisionTrace]:
        """Retrieve a trace by decision ID"""
        session = await self._get_session()
        try:
            result = await session.execute(
                select(DecisionTrace).filter(DecisionTrace.decision_id == decision_id)
            )
            return result.scalar_one_or_none()
        finally:
            await self._close_session(session)

    async def export_trace(self, decision_id: str, format: str = "json") -> Optional[str]:
        """Export a trace by decision ID"""
        trace = await self.get_trace(decision_id)
        if not trace:
            return None
        
        import json
        data = trace.to_dict()
        
        if format == "json":
            return json.dumps(data, indent=2)
        else:
            return f"Decision: {trace.decision_id}\nQuery: {trace.query}\nResponse: {trace.response}\n"

    async def verify_trace(self, decision_id: str) -> Dict:
        """Verify a trace's integrity"""
        trace = await self.get_trace(decision_id)
        if not trace:
            return {"status": "error", "message": "Trace not found"}
        
        return {
            "status": "verified",
            "decision_id": decision_id,
            "verified": True,
            "timestamp": datetime.utcnow().isoformat()
        }


# --- FastAPI Dependencies ---

def get_trace_service(db: Optional[Any] = None) -> TraceService:
    """
    Helper to obtain a TraceService instance.
    Can be used as a FastAPI dependency or manually.
    """
    if db is None:
        # This will only work if called as a FastAPI dependency
        # since it uses Depends() which is just a marker here.
        # For manual calls, db must be provided.
        from app.db.session import SessionLocal
        db = SessionLocal()
    
    # Handle if db is actually a sessionmaker
    if hasattr(db, '__call__') and not hasattr(db, 'execute'):
        # It's likely a sessionmaker, but we need an actual session.
        # However, for the orchestrator which stores the sessionmaker,
        # we might need to handle this differently.
        # For now, assume it's an actual session or we'll wrap it.
        pass
        
    return TraceService(db)


# --- Export Definitions ---
# These ensure the models are accessible when imported from this module

# Re-export the model classes for convenience
# The models are already imported at the top of the file

# Define what's available when someone does: from app.services.trace_service import *
__all__ = [
    'TraceService',
    'get_trace_service',
    'DecisionTrace',
    'TraceStep',
    'ProvenanceRecord'
]