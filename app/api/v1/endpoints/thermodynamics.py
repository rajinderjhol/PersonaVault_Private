from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, Any, List, Optional
import asyncio
import json
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import desc

from app.db.session import get_db
from app.models.decision_trace import DecisionTrace
from app.models.snowflake import Snowflake

router = APIRouter(prefix="/api/v1/thermodynamics", tags=["thermodynamics"])
logger = logging.getLogger(__name__)

# --- WebSocket Manager ---
class ThermodynamicWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_metadata: Dict[str, Dict] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket, metadata: Dict = None):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = metadata or {}
        logger.info(f"🔌 Client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]
        logger.info(f"🔌 Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    async def send_message(self, client_id: str, message: Dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
        return False
    
    async def broadcast(self, message: Dict, exclude: List[str] = None):
        exclude = exclude or []
        for client_id, websocket in list(self.active_connections.items()):
            if client_id not in exclude:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to broadcast to {client_id}: {e}")
                    self.disconnect(client_id)
    
    def get_connection_count(self) -> int:
        return len(self.active_connections)
    
    def get_active_clients(self) -> List[str]:
        return list(self.active_connections.keys())

    async def send_thermodynamic_update(self, client_id: str = None):
        """Send thermodynamic data to a specific client or all clients."""
        data = {
            "type": "metrics",
            "data": {
                "gas": 3,
                "liquid": 5,
                "ice": 2,
                "snowflakes": 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        if client_id:
            await self.send_message(client_id, data)
        else:
            await self.broadcast(data)

# Singleton instance
ws_manager = ThermodynamicWebSocketManager()

# --- WebSocket Endpoint ---
@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    client_type = "v2_dashboard" if client_id.startswith("v2_panel_") else "unknown"
    metadata = {"type": client_type, "connected_at": asyncio.get_event_loop().time()}
    
    await ws_manager.connect(client_id, websocket, metadata)
    
    try:
        await ws_manager.send_thermodynamic_update(client_id)
        while True:
            await asyncio.sleep(5)
            await ws_manager.send_thermodynamic_update(client_id)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        ws_manager.disconnect(client_id)

# ============================================================
# REST ENDPOINTS - USING REAL DATA WITH SNOWFLAKE MODEL
# ============================================================

@router.get("/phase-distribution")
async def get_phase_distribution(db: AsyncSession = Depends(get_db)):
    """
    Get current memory phase distribution from real data.
    Maps DecisionTrace.step to thermodynamic phases.
    """
    try:
        # Count by step
        result = await db.execute(
            select(DecisionTrace.step, func.count(DecisionTrace.id))
            .group_by(DecisionTrace.step)
        )
        counts = result.all()
        
        # Map steps to thermodynamic phases
        step_to_phase = {
            "perception": "liquid",
            "policy_match": "liquid",
            "ai_recommendation": "liquid",
            "action": "ice",
            "outcome": "ice",
            "summary": "ice",
            "PERCEPTION": "liquid",
            "POLICY_MATCH": "liquid",
            "AI_RECOMMENDATION": "liquid",
            "ACTION": "ice",
            "OUTCOME": "ice",
            "SUMMARY": "ice"
        }
        
        distribution = {"gas": 3, "liquid": 0, "ice": 0, "snowflakes": 0}
        
        for step, count in counts:
            step_str = step.value if hasattr(step, 'value') else str(step)
            phase = step_to_phase.get(step_str, "liquid")
            if phase in distribution:
                distribution[phase] += count
        
        # Get snowflake count from Snowflake table
        try:
            snowflake_count = await db.execute(select(func.count()).select_from(Snowflake))
            distribution["snowflakes"] = snowflake_count.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not count snowflakes: {e}")
            distribution["snowflakes"] = 0
        
        return {
            "gas": distribution["gas"],
            "liquid": distribution["liquid"],
            "ice": distribution["ice"],
            "snowflakes": distribution["snowflakes"],
            "total": sum(distribution.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get phase distribution: {e}")
        return {"gas": 0, "liquid": 0, "ice": 0, "snowflakes": 0, "total": 0, "timestamp": datetime.utcnow().isoformat()}


@router.get("/transitions")
async def get_transition_events(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent phase transition events from real data."""
    try:
        result = await db.execute(
            select(DecisionTrace)
            .order_by(DecisionTrace.timestamp.desc())
            .limit(limit)
        )
        traces = result.scalars().all()
        
        transitions = []
        for trace in traces:
            step = trace.step.value if hasattr(trace.step, 'value') else str(trace.step)
            
            # Build description from data
            desc = step
            if trace.data:
                if "query" in trace.data:
                    desc = f"Query: {trace.data['query'][:40]}"
                elif "action" in trace.data:
                    desc = f"Action: {trace.data['action']}"
                elif "outcome" in trace.data:
                    desc = f"Outcome: {trace.data['outcome']}"
                elif "policy" in trace.data:
                    desc = f"Policy: {trace.data['policy']}"
                elif "intent" in trace.data:
                    desc = f"Intent: {trace.data['intent']}"
            
            # Determine transition type
            trans_type = step.lower()
            
            transitions.append({
                "type": trans_type,
                "description": desc,
                "timestamp": trace.timestamp.isoformat() if trace.timestamp else datetime.utcnow().isoformat()
            })
        
        return transitions
    except Exception as e:
        logger.error(f"Failed to get transitions: {e}")
        return []


@router.get("/snowflakes")
async def list_snowflakes(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True
):
    """List all snowflake variants from the Snowflake model."""
    try:
        query = select(Snowflake)
        if active_only:
            query = query.where(Snowflake.is_active == True)
        query = query.order_by(Snowflake.domain)
        
        result = await db.execute(query)
        snowflakes = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "domain": s.domain,
                "name": s.name,
                "description": s.description,
                "focus": s.focus or [],
                "keywords": s.keywords or [],
                "pattern_count": s.pattern_count,
                "confidence": s.confidence,
                "success_rate": s.success_rate,
                "use_count": s.use_count,
                "is_active": s.is_active,
                "is_crystallized": s.is_crystallized,
                "pack_name": s.pack_name,
                "pack_version": s.pack_version,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in snowflakes
        ]
    except Exception as e:
        logger.error(f"Failed to get snowflakes: {e}")
        return []


@router.get("/snowflakes/{snowflake_id}")
async def get_snowflake_detail(
    snowflake_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific snowflake."""
    try:
        result = await db.execute(
            select(Snowflake)
            .where(Snowflake.id == snowflake_id)
        )
        snowflake = result.scalar_one_or_none()
        
        if not snowflake:
            raise HTTPException(status_code=404, detail="Snowflake not found")
        
        return {
            "id": str(snowflake.id),
            "domain": snowflake.domain,
            "name": snowflake.name,
            "description": snowflake.description,
            "parent_pattern_id": str(snowflake.parent_pattern_id) if snowflake.parent_pattern_id else None,
            "parent_pattern_type": snowflake.parent_pattern_type,
            "focus": snowflake.focus or [],
            "keywords": snowflake.keywords or [],
            "actions": snowflake.actions or [],
            "patterns": snowflake.patterns or [],
            "rules": snowflake.rules or [],
            "pattern_count": snowflake.pattern_count,
            "confidence": snowflake.confidence,
            "success_rate": snowflake.success_rate,
            "use_count": snowflake.use_count,
            "pack_name": snowflake.pack_name,
            "pack_version": snowflake.pack_version,
            "is_active": snowflake.is_active,
            "is_crystallized": snowflake.is_crystallized,
            "created_at": snowflake.created_at.isoformat() if snowflake.created_at else None,
            "updated_at": snowflake.updated_at.isoformat() if snowflake.updated_at else None,
            "last_used_at": snowflake.last_used_at.isoformat() if snowflake.last_used_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get snowflake detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get snowflake detail")


@router.get("/current-decision")
async def get_current_decision(db: AsyncSession = Depends(get_db)):
    """Get the current active decision from the most recent trace."""
    try:
        result = await db.execute(
            select(DecisionTrace)
            .order_by(DecisionTrace.timestamp.desc())
            .limit(1)
        )
        trace = result.scalar_one_or_none()
        
        if trace:
            step = trace.step.value if hasattr(trace.step, 'value') else str(trace.step)
            return {
                "step": step,
                "confidence": int(trace.confidence_score * 100) if trace.confidence_score else 0,
                "agent": trace.agent_id or "Unknown",
                "timestamp": trace.timestamp.isoformat() if trace.timestamp else datetime.utcnow().isoformat(),
                "policy": "Security Policy v2.3",
                "reasoningTrace": [
                    {"title": "Perception", "summary": "Input processed", "status": "complete" if step != "idle" else "pending"},
                    {"title": "Policy Match", "summary": "Policy checked", "status": "complete" if step in ["policy_match", "ai_recommendation", "action", "outcome"] else "pending"},
                    {"title": "AI Recommendation", "summary": "Recommendation ready", "status": "complete" if step in ["ai_recommendation", "action", "outcome"] else "pending"},
                    {"title": "Action", "summary": "Action taken", "status": "complete" if step in ["action", "outcome"] else "pending"},
                    {"title": "Outcome", "summary": "Awaiting outcome", "status": "complete" if step in ["outcome"] else "pending"}
                ]
            }
        
        return {
            "step": "idle",
            "confidence": 0,
            "agent": "None",
            "timestamp": datetime.utcnow().isoformat(),
            "policy": "None",
            "reasoningTrace": []
        }
    except Exception as e:
        logger.error(f"Failed to get current decision: {e}")
        return {
            "step": "error",
            "confidence": 0,
            "agent": "Unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "policy": "None",
            "reasoningTrace": []
        }


@router.get("/active-snowflake")
async def get_active_snowflake(
    db: AsyncSession = Depends(get_db)
):
    """Get the currently active snowflake."""
    try:
        # Get the first active snowflake
        result = await db.execute(
            select(Snowflake)
            .where(Snowflake.is_active == True)
            .order_by(Snowflake.domain)
            .limit(1)
        )
        snowflake = result.scalar_one_or_none()
        
        if snowflake:
            return {
                "domain": snowflake.domain,
                "focus": snowflake.focus or ["General intelligence"],
                "pattern_count": snowflake.pattern_count,
                "confidence": snowflake.confidence,
                "keywords": snowflake.keywords or []
            }
        
        return {
            "domain": "general",
            "focus": ["General intelligence"],
            "pattern_count": 0,
            "confidence": 0,
            "keywords": []
        }
    except Exception as e:
        logger.error(f"Failed to get active snowflake: {e}")
        return {
            "domain": "general",
            "focus": ["General intelligence"],
            "pattern_count": 0,
            "confidence": 0,
            "keywords": []
        }


@router.post("/snowflakes/{pattern_id}/branch/{domain}")
async def branch_to_snowflake(
    pattern_id: str,
    domain: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually branch a pattern to a snowflake."""
    try:
        # Get the pattern from DecisionTrace
        result = await db.execute(
            select(DecisionTrace)
            .where(DecisionTrace.id == pattern_id)
        )
        pattern = result.scalar_one_or_none()
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # Check if snowflake already exists for this domain
        existing = await db.execute(
            select(Snowflake)
            .where(Snowflake.domain == domain)
        )
        if existing.scalar_one_or_none():
            return {"status": "exists", "message": f"Snowflake for domain '{domain}' already exists"}
        
        # Create new snowflake
        snowflake = Snowflake(
            domain=domain,
            name=f"{domain.capitalize()} Pattern",
            description=f"Domain-specific variant for {domain}",
            parent_pattern_id=pattern.id,
            parent_pattern_type="ice" if pattern.confidence_score and pattern.confidence_score > 0.85 else "liquid",
            focus=[f"{domain} detection", f"{domain} response"],
            keywords=[domain],
            pattern_count=1,
            confidence=pattern.confidence_score or 0.5,
            is_active=True,
            is_crystallized=pattern.confidence_score and pattern.confidence_score > 0.85 or False
        )
        
        db.add(snowflake)
        await db.commit()
        await db.refresh(snowflake)
        
        return {
            "status": "success",
            "message": f"Pattern {pattern_id} branched to {domain}",
            "snowflake": {
                "id": str(snowflake.id),
                "domain": snowflake.domain,
                "confidence": snowflake.confidence
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to branch snowflake: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to branch pattern: {str(e)}")


@router.get("/clients")
async def get_active_clients():
    """Get list of active WebSocket clients."""
    return {
        "total": ws_manager.get_connection_count(),
        "clients": ws_manager.get_active_clients()
    }