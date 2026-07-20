import os
import logging
from neo4j import GraphDatabase
from config import Config
from typing import List, Dict

logger = logging.getLogger(__name__)

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

    def create_memory_node(self, memory_id: int, title: str, user_id: int):
        """Create a memory node in Neo4j."""
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                session.run(
                    "MERGE (m:Memory {id: $id}) SET m.title = $title, m.user_id = $user_id",
                    id=memory_id, title=title, user_id=user_id
                )
        except Exception as e:
            logger.error(f"GraphService: Error creating node for memory_id={memory_id}: {e}")

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
