from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

async def global_exception_handler(request: Request, exc: Exception):
    """Unified error response for the entire PersonaVault ecosystem."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "code": "INTERNAL_SERVER_ERROR",
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.state.request_id if hasattr(request.state, 'request_id') else "N/A"
        },
    )