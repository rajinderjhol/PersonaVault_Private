from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/models", tags=["models"])

@router.get("/")
async def get_models(current_user = Depends(get_current_user)):
    """Returns a list of available AI models."""
    return [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        {"id": "ollama-tinydolphin", "name": "Ollama TinyDolphin"}
    ]
