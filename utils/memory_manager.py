import sqlite3
import uuid
import json
import requests
import numpy as np
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants
OLLAMA_URL = "http://localhost:11434/api/embeddings"  # URL for Ollama embeddings API
EMBEDDING_MODEL = "llama2"  # Model used for generating embeddings

# ==================== //
# Utility Functions
# ==================== //

def cosine_similarity(vec1, vec2):
    """
    Compute the cosine similarity between two vectors.

    Args:
        vec1 (np.array): The first vector.
        vec2 (np.array): The second vector.

    Returns:
        float: The cosine similarity between the two vectors.
    """
    try:
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        similarity = dot_product / (norm_vec1 * norm_vec2)
        logger.debug(f"Computed cosine similarity: {similarity}")
        return similarity
    except Exception as e:
        logger.error(f"Error computing cosine similarity: {e}")
        raise

def generate_embedding(content):
    """
    Generate an embedding for the given content using Ollama.

    Args:
        content (str): The content to generate an embedding for.

    Returns:
        np.array: The embedding vector.

    Raises:
        Exception: If there is an error generating the embedding.
    """
    try:
        payload = {
            "model": EMBEDDING_MODEL,
            "prompt": content
        }
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        embedding = response.json().get("embedding")
        if not embedding:
            raise ValueError("No embedding found in the response.")
        logger.debug(f"Generated embedding for content: {content}")
        return np.array(embedding)
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

@contextmanager
def get_db_connection():
    """
    Context manager for handling database connections.

    Yields:
        sqlite3.Connection: A connection to the SQLite database.

    Raises:
        sqlite3.Error: If there is an error connecting to the database.
    """
    conn = None
    try:
        conn = sqlite3.connect("memory_db/personavault.db", detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# ==================== //
# Memory Management Functions
# ==================== //

def save_memory(user_id, memory_type, content, tags=None, privacy_level="public", expiry_days=7):
    """
    Save a memory to the database with an embedding.

    Args:
        user_id (str): The ID of the user saving the memory.
        memory_type (str): The type of memory (e.g., "development", "personal").
        content (str): The content of the memory (e.g., a code snippet or note).
        tags (list, optional): A list of tags associated with the memory. Defaults to None.
        privacy_level (str, optional): The privacy level of the memory ("public" or "private"). Defaults to "public".
        expiry_days (int, optional): The number of days until the memory expires. Defaults to 7.

    Returns:
        str: The ID of the saved memory.

    Raises:
        Exception: If there is an error saving the memory.
    """
    try:
        memory_id = str(uuid.uuid4())
        embedding = generate_embedding(content)  # Generate embedding
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memories (id, user_id, memory_type, content, tags, privacy_level, expiry_days, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (memory_id, user_id, memory_type, content, json.dumps(tags) if tags else None, privacy_level, expiry_days, json.dumps(embedding.tolist())))
            conn.commit()
        logger.info(f"Memory saved successfully: {memory_id}")
        return memory_id
    except Exception as e:
        logger.error(f"Error saving memory: {e}")
        raise

def get_memories(user_id, memory_type=None, privacy_level=None):
    """
    Retrieve memories for a specific user, optionally filtered by memory_type and privacy_level.

    Args:
        user_id (str): The ID of the user whose memories are being retrieved.
        memory_type (str, optional): Filter memories by type (e.g., "development"). Defaults to None.
        privacy_level (str, optional): Filter memories by privacy level ("public" or "private"). Defaults to None.

    Returns:
        list: A list of memories matching the criteria.

    Raises:
        Exception: If there is an error retrieving memories.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM memories WHERE user_id = ?"
            params = [user_id]

            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)
            if privacy_level:
                query += " AND privacy_level = ?"
                params.append(privacy_level)

            cursor.execute(query, params)
            memories = cursor.fetchall()
        logger.info(f"Retrieved {len(memories)} memories for user: {user_id}")
        return memories
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        raise

def search_memories(user_id, query, top_k=5, memory_type=None):
    """
    Retrieve the top-k most relevant memories for a query using semantic search.

    Args:
        user_id (str): The ID of the user whose memories are being searched.
        query (str): The query to search for.
        top_k (int, optional): The number of top results to return. Defaults to 5.
        memory_type (str, optional): Filter memories by type (e.g., "development"). Defaults to None.

    Returns:
        list: A list of dictionaries containing the memory ID, content, and similarity score.

    Raises:
        Exception: If there is an error searching memories.
    """
    try:
        query_embedding = generate_embedding(query)  # Generate embedding for the query
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Fetch memories, optionally filtered by memory_type
            if memory_type:
                cursor.execute('SELECT id, content, embedding FROM memories WHERE user_id = ? AND memory_type = ?', (user_id, memory_type))
            else:
                cursor.execute('SELECT id, content, embedding FROM memories WHERE user_id = ?', (user_id,))
            memories = cursor.fetchall()

        # Calculate cosine similarity between query and memories
        similarities = []
        for memory in memories:
            memory_id, content, embedding_json = memory
            memory_embedding = np.array(json.loads(embedding_json))
            similarity = cosine_similarity(query_embedding, memory_embedding)
            similarities.append((memory_id, content, similarity))

        # Sort by similarity and return top-k results
        similarities.sort(key=lambda x: x[2], reverse=True)
        top_results = [{"id": mem[0], "content": mem[1], "similarity": mem[2]} for mem in similarities[:top_k]]
        logger.info(f"Found {len(top_results)} relevant memories for query: {query}")
        return top_results
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise

def delete_expired_memories():
    """
    Delete memories that have expired.

    Raises:
        Exception: If there is an error deleting expired memories.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM memories
                WHERE expiry_days > 0 AND created_at <= DATE('now', '-' || expiry_days || ' days')
            ''')
            conn.commit()
        logger.info("Expired memories deleted successfully.")
    except Exception as e:
        logger.error(f"Error deleting expired memories: {e}")
        raise