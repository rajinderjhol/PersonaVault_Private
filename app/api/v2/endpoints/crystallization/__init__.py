from fastapi import APIRouter
from . import routes

router = APIRouter(prefix="/crystallization", tags=["v2-crystallization"])
router.include_router(routes.router)
