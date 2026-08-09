import logging
import functools
import time
from typing import List, Dict, Any
from neo4j import GraphDatabase
from app.repositories.interfaces import IGraphRepository
from app.config import Config

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    if not self.driver:
                        self._connect()
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                        self._connect()
            return False if func.__name__.startswith('add') else []
        return wrapper
    return decorator

class Neo4jGraphRepository(IGraphRepository):
    """Neo4j implementation for relationship memory."""
    
    def __init__(self):
        self.driver = None
        self._connect()
    
    def _connect(self):
        try:
            self.driver = GraphDatabase.driver(
                Config.NEO4J_URL, 
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
            )
        except Exception as e:
            logger.warning(f"Neo4jGraphRepository: Connection failed: {e}")
            self.driver = None

    @retry_on_failure()
    async def add_node(self, entity_id: int, entity_name: str, entity_type: str, user_id: int) -> bool:
        if not self.driver: return False
        with self.driver.session() as session:
            session.run(
                f"MERGE (n:`{entity_type}` {{id: $id}}) SET n.name = $name, n.user_id = $user_id",
                id=entity_id, name=entity_name, user_id=user_id
            )
            return True

    @retry_on_failure()
    async def add_relation(self, source_id: int, target_id: int, relation_type: str) -> bool:
        if not self.driver: return False
        with self.driver.session() as session:
            query = f"MATCH (a) WHERE a.id = $id1 MATCH (b) WHERE b.id = $id2 MERGE (a)-[:`{relation_type}`]->(b)"
            session.run(query, id1=source_id, id2=target_id)
            return True

    @retry_on_failure()
    async def get_neighbors(self, entity_id: int, depth: int = 1) -> List[Any]:
        if not self.driver: return []
        with self.driver.session() as session:
            query = "MATCH (n {id: $id})-[r*1..%d]-(m) RETURN m" % depth
            result = session.run(query, id=entity_id)
            return [record.data() for record in result]

    @retry_on_failure()
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        if not self.driver: return []
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
