import os
import logging
import time
import functools
from neo4j import GraphDatabase
from app.config import Config
from typing import List, Dict

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry Neo4j operations with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    if not self.driver:
                        self._connect()
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"GraphService: Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                        if any(k in str(e).lower() for k in ["connection", "unavailable", "expired"]):
                            self._connect()
            logger.error(f"GraphService: All {max_retries} retries failed for {func.__name__}: {last_error}")
            return [] if func.__name__ == 'execute_query' else None
        return wrapper
    return decorator

class GraphService:
    """Service for managing relational memory patterns in Neo4j."""
    def __init__(self):
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database."""
        try: # Use Config for Neo4j credentials
            uri = Config.NEO4J_URL
            user = Config.NEO4J_USER
            password = Config.NEO4J_PASSWORD
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info("GraphService: Established connection to Neo4j")
        except Exception as e:
            logger.warning(f"GraphService: Neo4j connection failed: {e}. Relational features disabled.")
            self.driver = None

    @retry_on_failure(max_retries=3, delay=1)
    def create_decision_node(self, decision_id: str, query: str, pack: str, timestamp: str, confidence: float):
        """Create a decision node in Neo4j."""
        if not self.driver: return
        with self.driver.session() as session:
            session.run(
                "MERGE (d:Decision {id: $id}) SET d.query = $query, d.pack = $pack, d.timestamp = $timestamp, d.confidence = $confidence",
                id=decision_id, query=query, pack=pack, timestamp=timestamp, confidence=confidence
            )

    @retry_on_failure(max_retries=3, delay=1)
    def create_evidence_node(self, evidence_id: str, source_type: str, quality_score: float):
        """Create an evidence node in Neo4j."""
        if not self.driver: return
        with self.driver.session() as session:
            session.run(
                "MERGE (e:Evidence {id: $id}) SET e.source_type = $source_type, e.quality_score = $quality_score",
                id=evidence_id, source_type=source_type, quality_score=quality_score
            )

    @retry_on_failure(max_retries=3, delay=1)
    def link_decision_to_evidence(self, decision_id: str, evidence_id: str):
        """Create a USES_EVIDENCE relationship."""
        if not self.driver: return
        with self.driver.session() as session:
            session.run(
                "MATCH (d:Decision {id: $did}), (e:Evidence {id: $eid}) MERGE (d)-[:USES_EVIDENCE]->(e)",
                did=decision_id, eid=evidence_id
            )

    @retry_on_failure(max_retries=3, delay=1)
    def link_decision_to_policy(self, decision_id: str, policy_key: str):
        """Create a FOLLOWS_POLICY relationship."""
        if not self.driver: return
        with self.driver.session() as session:
            session.run(
                "MATCH (d:Decision {id: $did}) MERGE (p:Policy {key: $pk}) MERGE (d)-[:FOLLOWS_POLICY]->(p)",
                did=decision_id, pk=policy_key
            )

    @retry_on_failure(max_retries=3, delay=1)
    def create_relationship(self, memory_id1: int, memory_id2: int, relation_type: str):
        """Creates a directional relationship between two memory nodes."""
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                # Relation types must be injected directly into Cypher (use backticks for safety)
                query = f"MATCH (a:Memory {{id: $id1}}), (b:Memory {{id: $id2}}) MERGE (a)-[:`{relation_type}`]->(b)"
                session.run(query, id1=memory_id1, id2=memory_id2)
                logger.info(f"GraphService: Linked {memory_id1} -> {memory_id2} type='{relation_type}'")
        except Exception as e:
            logger.error(f"GraphService: Error creating relationship: {e}")

    @retry_on_failure(max_retries=3, delay=1)
    def execute_query(self, query: str) -> List[Dict]:
        """Execute a Cypher query."""
        if not self.driver:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []

    def check_health(self) -> bool:
        """Verify Neo4j connectivity."""
        if not self.driver:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("GraphService: Connection closed.")
# Instantiate a global service instance for use throughout the application
graph_service = GraphService()
