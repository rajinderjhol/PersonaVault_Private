"""
Data Lineage Service - Track data provenance and handle deletion requests
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import json

from app.models.lineage import (
    LineageNode, LineageEdge, DeletionRequest, DeletionResult,
    SourceType
)
from app.services.memory.ice_repository import IceMemoryRepository
from app.services.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)


class LineageService:
    """
    Service for tracking data lineage and handling deletion requests.
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.lineage_path = Path("data/lineage")
        self.lineage_path.mkdir(parents=True, exist_ok=True)
        self.nodes_path = self.lineage_path / "nodes.json"
        self.edges_path = self.lineage_path / "edges.json"
        self.requests_path = self.lineage_path / "deletion_requests.json"
        
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []
        self.requests: List[DeletionRequest] = []
        
        self._load_state()
    
    def _load_state(self):
        """Load lineage state from disk."""
        if self.nodes_path.exists():
            try:
                with open(self.nodes_path, 'r') as f:
                    data = json.load(f)
                    self.nodes = {
                        k: LineageNode(**v) for k, v in data.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load nodes: {e}")
        
        if self.edges_path.exists():
            try:
                with open(self.edges_path, 'r') as f:
                    data = json.load(f)
                    self.edges = [LineageEdge(**e) for e in data]
            except Exception as e:
                logger.error(f"Failed to load edges: {e}")
        
        if self.requests_path.exists():
            try:
                with open(self.requests_path, 'r') as f:
                    data = json.load(f)
                    self.requests = [DeletionRequest(**r) for r in data]
            except Exception as e:
                logger.error(f"Failed to load requests: {e}")
        
        logger.info(f"Loaded {len(self.nodes)} nodes, {len(self.edges)} edges, {len(self.requests)} deletion requests")
    
    def _save_state(self):
        """Save lineage state to disk."""
        try:
            with open(self.nodes_path, 'w') as f:
                json.dump(
                    {k: v.dict() for k, v in self.nodes.items()},
                    f,
                    indent=2,
                    default=str
                )
            
            with open(self.edges_path, 'w') as f:
                json.dump(
                    [e.dict() for e in self.edges],
                    f,
                    indent=2,
                    default=str
                )
            
            with open(self.requests_path, 'w') as f:
                json.dump(
                    [r.dict() for r in self.requests],
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(f"Failed to save lineage state: {e}")
    
    async def track_node(
        self,
        node_type: SourceType,
        user_id: Optional[int] = None,
        source_id: Optional[str] = None,
        content_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> LineageNode:
        """Track a new data node."""
        node_id = f"{node_type.value}_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        node = LineageNode(
            id=node_id,
            type=node_type,
            created_at=datetime.now(),
            source_id=source_id,
            user_id=user_id,
            content_summary=content_summary[:200],
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        self._save_state()
        
        logger.info(f"Tracked node: {node_id} ({node_type.value})")
        return node
    
    async def track_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        relationship: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LineageEdge:
        """Track a relationship between two nodes."""
        edge = LineageEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship=relationship,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.edges.append(edge)
        self._save_state()
        
        logger.info(f"Tracked edge: {source_node_id} -> {target_node_id} ({relationship})")
        return edge
    
    async def get_lineage(
        self,
        node_id: str,
        depth: int = 3
    ) -> Dict[str, Any]:
        """Get the full lineage graph for a node."""
        visited = set()
        graph = {
            "nodes": {},
            "edges": []
        }
        
        async def traverse(current_id: str, current_depth: int):
            if current_id in visited or current_depth > depth:
                return
            
            visited.add(current_id)
            
            # Add node
            if current_id in self.nodes:
                graph["nodes"][current_id] = self.nodes[current_id].dict()
            
            # Find related edges
            related_edges = [
                e for e in self.edges
                if e.source_node_id == current_id or e.target_node_id == current_id
            ]
            
            for edge in related_edges:
                graph["edges"].append(edge.dict())
                
                # Traverse connected nodes
                next_node = (
                    edge.target_node_id
                    if edge.source_node_id == current_id
                    else edge.source_node_id
                )
                if next_node not in visited:
                    await traverse(next_node, current_depth + 1)
        
        await traverse(node_id, 0)
        
        return {
            "root_node": node_id,
            "depth": depth,
            "nodes_count": len(graph["nodes"]),
            "edges_count": len(graph["edges"]),
            "graph": graph
        }
    
    async def get_user_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get all data for a user."""
        user_nodes = [
            node for node in self.nodes.values()
            if node.user_id == user_id
        ]
        
        user_edges = [
            edge for edge in self.edges
            if edge.source_node_id in [n.id for n in user_nodes]
            or edge.target_node_id in [n.id for n in user_nodes]
        ]
        
        return {
            "user_id": user_id,
            "nodes": [n.dict() for n in user_nodes],
            "edges": [e.dict() for e in user_edges],
            "node_count": len(user_nodes),
            "edge_count": len(user_edges)
        }
    
    async def create_deletion_request(
        self,
        user_id: int,
        target_ids: List[str],
        request_type: str = "delete_user_data",
        explanation: Optional[str] = None
    ) -> DeletionRequest:
        """Create a deletion request for a user."""
        request = DeletionRequest(
            id=f"del_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            request_type=request_type,
            target_ids=target_ids,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            audit_log=[],
            explanation=explanation
        )
        
        self.requests.append(request)
        self._save_state()
        
        logger.info(f"Created deletion request: {request.id} for user {user_id}")
        return request
    
    async def process_deletion_request(
        self,
        request_id: str
    ) -> DeletionResult:
        """Process a deletion request."""
        request = next(
            (r for r in self.requests if r.id == request_id),
            None
        )
        if not request:
            raise ValueError(f"Deletion request {request_id} not found")
        
        request.status = "processing"
        request.updated_at = datetime.now()
        request.audit_log.append({
            "action": "processing_started",
            "timestamp": datetime.now().isoformat()
        })
        self._save_state()
        
        deleted_nodes = []
        invalidated_patterns = []
        errors = []
        
        try:
            # Process each target
            for target_id in request.target_ids:
                if target_id in self.nodes:
                    node = self.nodes[target_id]
                    
                    # If this is a pattern node, invalidate it
                    if node.type == SourceType.PATTERN:
                        invalidated_patterns.append(target_id)
                        await self._invalidate_pattern(target_id)
                    
                    # Remove the node
                    del self.nodes[target_id]
                    deleted_nodes.append(target_id)
                    
                    # Remove related edges
                    self.edges = [
                        e for e in self.edges
                        if e.source_node_id != target_id
                        and e.target_node_id != target_id
                    ]
            
            # Also handle all descendant nodes
            descendants = await self._get_descendants(request.target_ids)
            for desc_id in descendants:
                if desc_id in self.nodes:
                    node = self.nodes[desc_id]
                    if node.type == SourceType.PATTERN:
                        invalidated_patterns.append(desc_id)
                        await self._invalidate_pattern(desc_id)
                    del self.nodes[desc_id]
                    deleted_nodes.append(desc_id)
            
            # Mark request as completed
            request.status = "completed"
            request.completed_at = datetime.now()
            request.audit_log.append({
                "action": "processing_completed",
                "timestamp": datetime.now().isoformat(),
                "deleted_nodes": deleted_nodes,
                "invalidated_patterns": invalidated_patterns
            })
            
            self._save_state()
            
            return DeletionResult(
                request_id=request_id,
                success=True,
                deleted_nodes=deleted_nodes,
                invalidated_patterns=invalidated_patterns,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            request.status = "failed"
            request.updated_at = datetime.now()
            request.audit_log.append({
                "action": "processing_failed",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            self._save_state()
            
            return DeletionResult(
                request_id=request_id,
                success=False,
                errors=[str(e)],
                completed_at=datetime.now()
            )
    
    async def _invalidate_pattern(self, pattern_id: str):
        """Invalidate a crystallized pattern."""
        try:
            ice_repo = IceMemoryRepository(self.session_factory)
            await ice_repo.mark_invalid(pattern_id)
            logger.info(f"Invalidated pattern: {pattern_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern_id}: {e}")
    
    async def _get_descendants(self, node_ids: List[str]) -> List[str]:
        """Get all descendants of a set of nodes."""
        descendants = []
        to_process = list(node_ids)
        
        while to_process:
            current = to_process.pop()
            children = [
                e.target_node_id for e in self.edges
                if e.source_node_id == current
            ]
            for child in children:
                if child not in descendants and child not in node_ids:
                    descendants.append(child)
                    to_process.append(child)
        
        return descendants
    
    async def get_deletion_request_status(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """Get the status of a deletion request."""
        request = next(
            (r for r in self.requests if r.id == request_id),
            None
        )
        if not request:
            raise ValueError(f"Deletion request {request_id} not found")
        
        return {
            "id": request.id,
            "user_id": request.user_id,
            "status": request.status,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "completed_at": request.completed_at,
            "audit_log": request.audit_log,
            "target_count": len(request.target_ids)
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get lineage statistics."""
        user_nodes = {}
        pattern_nodes = 0
        memory_nodes = 0
        
        for node in self.nodes.values():
            if node.type == SourceType.PATTERN:
                pattern_nodes += 1
            elif node.type == SourceType.MEMORY:
                memory_nodes += 1
            
            if node.user_id:
                user_nodes[node.user_id] = user_nodes.get(node.user_id, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "pattern_nodes": pattern_nodes,
            "memory_nodes": memory_nodes,
            "user_nodes": user_nodes,
            "deletion_requests": {
                "total": len(self.requests),
                "pending": len([r for r in self.requests if r.status == "pending"]),
                "completed": len([r for r in self.requests if r.status == "completed"]),
                "failed": len([r for r in self.requests if r.status == "failed"])
            }
        }
