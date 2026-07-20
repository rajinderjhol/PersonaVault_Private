from transformers import pipeline
import numpy as np

# Load a pre-trained model for embeddings
model = pipeline('feature-extraction', model='distilbert-base-uncased')

def find_relevant_memories(query: str, memories: list, top_k: int = 5):
    """
    Find the top-k most relevant memories for a given query using embeddings.
    """
    try:
        # Get the embedding for the query
        query_embedding = np.array(model(query)[0][0])  # Use the first token's embedding

        # Get embeddings for all memories
        memory_embeddings = [np.array(model(memory.content)[0][0]) for memory in memories]

        # Calculate cosine similarity between the query and each memory
        similarities = [np.dot(query_embedding, mem_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(mem_embedding))
                        for mem_embedding in memory_embeddings]

        # Sort memories by similarity and return the top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]  # Get top-k indices
        return [memories[i] for i in top_indices]
    except Exception as e:
        print(f"Error in semantic search: {e}")
        raise