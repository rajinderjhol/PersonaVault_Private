from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Basic API Config
    PROJECT_NAME: str = "PersonaVault"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./pv.db"
    
    # AI Providers
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_DIM: int = 4096
    
    # Privacy & Security
    ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520
    
    # Cognitive Thresholds
    CONFIDENCE_THRESHOLD_HITL: float = 0.6
    GRADUATION_BATCH_SIZE: int = 10
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()