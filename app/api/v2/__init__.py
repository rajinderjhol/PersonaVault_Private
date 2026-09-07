from fastapi import APIRouter

# Only import routers that don't cause circular imports
from app.api.v2.endpoints import environments
from app.api.v2.endpoints import health as v2_health_router
from app.api.v2.endpoints import models as v2_models_router
from app.api.v2.endpoints import ingestion as v2_ingestion_router
from app.api.v2.endpoints import search as v2_search_router
# NOTE: chat is removed to avoid circular import

router = APIRouter()

router.include_router(environments.router, prefix="/environments", tags=["V2 Environments"])
router.include_router(v2_health_router.router, prefix="/health", tags=["V2 Health"])
router.include_router(v2_models_router.router, prefix="/models", tags=["V2 Models"])
router.include_router(v2_ingestion_router.router, prefix="/ingestion", tags=["V2 Ingestion"])
router.include_router(v2_search_router.router, prefix="/search", tags=["V2 Search"])
