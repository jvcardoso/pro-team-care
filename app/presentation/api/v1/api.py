from fastapi import APIRouter

from . import auth, health, metrics, companies, cnpj, geocoding

api_router = APIRouter()

# Include route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["monitoring"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(cnpj.router, prefix="/cnpj", tags=["cnpj"])
api_router.include_router(geocoding.router, prefix="/geocoding", tags=["geocoding"])