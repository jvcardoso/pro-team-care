from fastapi import APIRouter

from . import auth, health, metrics, companies, cnpj, geocoding, menus, debug_menus, menus_crud, users, simple_db_admin, users_hierarchical, secure_sessions, establishments
# from . import db_admin  # Temporarily disabled due to import issues

api_router = APIRouter()

# Include route modules - Tags definidas nos arquivos individuais
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(health.router)
api_router.include_router(metrics.router)
api_router.include_router(companies.router, prefix="/companies")
api_router.include_router(cnpj.router, prefix="/cnpj")
api_router.include_router(geocoding.router, prefix="/geocoding")
api_router.include_router(menus.router)
api_router.include_router(menus_crud.router) # HABILITADO - compatível com schema atual após correções
api_router.include_router(debug_menus.debug_router)
api_router.include_router(users.router, prefix="/users") # CRUD de usuários - production ready
api_router.include_router(establishments.router, prefix="/establishments") # CRUD de estabelecimentos - production ready
api_router.include_router(users_hierarchical.router) # Sistema hierárquico de usuários
api_router.include_router(secure_sessions.router) # Sistema de sessões seguras com troca de perfil
api_router.include_router(simple_db_admin.router) # Simple Database Administration
# api_router.include_router(db_admin.router) # Administração do banco SQLAlchemy - Temporarily disabled