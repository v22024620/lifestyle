"""API router composition."""
from fastapi import APIRouter

from app.api.endpoints import studios, simulate

api_router = APIRouter()
api_router.include_router(studios.router, prefix="/studios", tags=["studios"])
api_router.include_router(simulate.router, prefix="/simulate", tags=["simulate"])
