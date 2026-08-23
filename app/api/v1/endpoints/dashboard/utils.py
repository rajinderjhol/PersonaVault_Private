from pathlib import Path
import time
import logging
import os
import shutil
import psutil
from datetime import datetime, timezone
from app.config import Config

logger = logging.getLogger(__name__)

def _safe_metric_get(metric, default=0, labels=None):
    try:
        if labels:
            return metric.labels(**labels)._value.get()
        if hasattr(metric, '_value') and hasattr(metric._value, 'get'):
            return metric._value.get()
        if hasattr(metric, 'value'):
            return metric.value
        return float(metric) if metric is not None else default
    except:
        return default

_ollama_cache = {
    "status": "unknown",
    "last_check": 0,
    "cache_ttl": 30
}

async def _check_ollama(request) -> bool:
    """Check Ollama service status with caching."""
    now = time.time()
    if now - _ollama_cache["last_check"] < _ollama_cache["cache_ttl"]:
        return _ollama_cache["status"]

    try:
        res = await request.app.state.ai_client.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=1.0)
        if res.status_code == 200:
            models = res.json().get("models", [])
            _ollama_cache["status"] = f"connected ({len(models)} models)" if models else "connected (no models)"
        else:
            _ollama_cache["status"] = "error"
    except Exception as e:
        logger.warning(f"Ollama health check: service unreachable at {Config.OLLAMA_BASE_URL}")
        _ollama_cache["status"] = "disconnected"

    _ollama_cache["last_check"] = now
    return _ollama_cache["status"]

async def _check_gemini(request) -> str:
    """Check Gemini service status."""
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        return "not_configured"
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return "connected"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return "error"

async def _get_storage_usage() -> dict:
    """Get storage usage information."""
    home_dir = os.path.expanduser("~")
    # This might need adjustment based on how it was originally used in dashboard_router.py
    # Path(__file__).parents[4] might not be correct here.
    # Original used: Path(__file__).parents[4]
    # dashboard_router.py is in backend/app/api/v1/endpoints/dashboard/
    # parents[4] points to... 
    #   0: dashboard
    #   1: endpoints
    #   2: v1
    #   3: api
    #   4: app (wait, 4 is likely `backend`)
    project_dir = Path(__file__).parents[5] 
    
    def get_dir_size(path):
        total = 0
        if not os.path.exists(path):
            return 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except (FileNotFoundError, PermissionError):
                    continue
        return round(total / (1024**2), 2)

    try:
        total, used, free = shutil.disk_usage(home_dir)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_percent": round((used / total) * 100, 2) if total > 0 else 0,
            "breakdown_mb": {
                "venv": get_dir_size(project_dir / ".venv"),
                "uploads": get_dir_size(project_dir / "storage/uploads"),
                "vector_storage": get_dir_size(project_dir / "storage")
            },
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        return {"error": f"Storage diagnostics unavailable: {str(e)}"}

async def _get_cpu_usage() -> float:
    """Get CPU usage."""
    try:
        return psutil.cpu_percent(interval=None)
    except Exception as e:
        logger.warning(f"CPU metrics unavailable: {e}")
        return -1

async def _get_memory_usage() -> dict:
    """Get memory usage."""
    try:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "free_gb": round(mem.free / (1024**3), 2),
            "used_percent": mem.percent
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {"error": "Unable to retrieve system memory info"}
