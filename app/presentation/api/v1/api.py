from fastapi import APIRouter

from . import auth, health, metrics

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["monitoring"])