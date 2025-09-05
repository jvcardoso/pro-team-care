from fastapi import APIRouter

from . import auth, health, metrics, companies, cnpj, geocoding, menus, menus_crud

api_router = APIRouter()

# Include route modules - Tags definidas nos arquivos individuais
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(health.router)
api_router.include_router(metrics.router)
api_router.include_router(companies.router, prefix="/companies")
api_router.include_router(cnpj.router, prefix="/cnpj")
api_router.include_router(geocoding.router, prefix="/geocoding")
api_router.include_router(menus.router)
api_router.include_router(menus_crud.router)