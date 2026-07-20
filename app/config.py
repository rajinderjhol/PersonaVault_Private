import os
from enum import Enum
from dotenv import load_dotenv, find_dotenv

# Automatically find and load the .env file, searching upwards to the project root
load_dotenv(find_dotenv())

class InfrastructureMode(str, Enum):
    CONVERGED = "converged"     # SQL handles everything (Relational + Vector + Graph)
    DISTRIBUTED = "distributed" # specialized engines (SQL + Weaviate + Neo4j)

class Config:
    # --- Environment & Strategic Modes ---
    APP_ENV = os.getenv("APP_ENV", "development")
    INFRA_MODE = InfrastructureMode(os.getenv("INFRA_MODE", "converged"))
    CONNECTIVITY_MODE = os.getenv("CONNECTIVITY_MODE", "LOCAL")
    IS_AIR_GAPPED = os.getenv("IS_AIR_GAPPED", "false").lower() == "true"

    # --- Cryptography ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_me")

    # --- Database Configuration ---
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./storage/memory_db/personavault.db" 
    )

    # --- Specialized Engine Configuration ---
    VECTOR_ENGINE = os.getenv("VECTOR_ENGINE", "sql" if INFRA_MODE == InfrastructureMode.CONVERGED else "weaviate")
    GRAPH_ENGINE = os.getenv("GRAPH_ENGINE", "sql" if INFRA_MODE == InfrastructureMode.CONVERGED else "neo4j")

    # --- AI Service Configuration (Local Ollama) ---
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_URL", "http://localhost:11434"))
    OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "tinydolphin")
    OLLAMA_JUDGE_MODEL = os.getenv("OLLAMA_JUDGE_MODEL", "tinydolphin")
    OLLAMA_REASONER_MODEL = os.getenv("OLLAMA_REASONER_MODEL", "tinydolphin")
    
    # Embedding Configuration (Used by VectorService)
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_EMBEDDING_DIM = int(os.getenv("OLLAMA_EMBEDDING_DIM", "768"))

    # --- Specialized Database Credentials ---
    NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

    # --- Cloud AI (Gemini) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")