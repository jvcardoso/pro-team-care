from fastapi import APIRouter

from . import (
    auth,
    b2b_billing,
    billing,
    clients,
    cnpj,
    companies,
    company_activation,
    company_stats,
    contract_dashboard,
    contracts,
    dashboard,
    db_admin,
    establishments,
    geocoding,
    geolocation,
    health,
    limits_control,
    medical_authorizations,
    menus,
    menus_crud,
    menus_dynamic,
    menus_simple,
    metrics,
    notifications,
    password_reset,
    professionals,
    program_codes,
    roles,
    saas_billing,
    secure_sessions,
    system_optimization,
    user_activation,
    users,
    users_hierarchical,
)

# ALL MODULES NOW WORKING! ✅
# menus_dynamic, notifications, dashboard fixed with simplified versions

api_router = APIRouter()

# Include route modules - Tags definidas nos arquivos individuais
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(password_reset.router)  # Password reset endpoints
api_router.include_router(program_codes.router)  # Program codes (Ctrl+Alt+X navigation)
api_router.include_router(health.router)
api_router.include_router(metrics.router)
# Core business endpoints
api_router.include_router(companies.router, prefix="/companies")
api_router.include_router(company_stats.router, prefix="/companies", tags=["Companies"])
api_router.include_router(
    company_activation.router
)  # Ativação de empresas (novo fluxo)
api_router.include_router(users.router, prefix="/users")
api_router.include_router(user_activation.router)  # Ativação de usuários
api_router.include_router(establishments.router, prefix="/establishments")
api_router.include_router(roles.router, prefix="/roles")

# Client and Professional management
api_router.include_router(clients.router, prefix="/clients")
api_router.include_router(professionals.router, prefix="/professionals")

# Home Care Contracts
api_router.include_router(contracts.router, prefix="/contracts")
api_router.include_router(contracts.services_router, prefix="/services")
api_router.include_router(contract_dashboard.router)
api_router.include_router(medical_authorizations.router)
api_router.include_router(limits_control.router)

# Billing System
api_router.include_router(billing.router, prefix="/billing")  # Home Care Billing (B2C)
api_router.include_router(
    b2b_billing.router, prefix="/b2b-billing"
)  # Legacy B2B billing
api_router.include_router(
    saas_billing.router, prefix="/saas-billing"
)  # NEW: SaaS Billing (Company Subscriptions)

# Menu systems
api_router.include_router(menus.router, prefix="/menus")
api_router.include_router(menus_crud.router)  # CRUD completo de menus
api_router.include_router(
    menus_simple.router, prefix="/menus"
)  # Menus simples (fallback)
api_router.include_router(menus_simple.debug_router, prefix="")  # Endpoints de debug

# Security and sessions
api_router.include_router(secure_sessions.router)

# Additional services
api_router.include_router(geocoding.router, prefix="/geocoding")
api_router.include_router(geolocation.router, prefix="/geolocation")

# All modules now ACTIVE! 🎉
api_router.include_router(menus_dynamic.router, prefix="/menus-dynamic")
api_router.include_router(notifications.router, prefix="/notifications")
api_router.include_router(dashboard.router, prefix="/dashboard")

# Administrative endpoints
api_router.include_router(cnpj.router, prefix="/cnpj")  # Consulta CNPJ
api_router.include_router(db_admin.router)  # Administração do banco
api_router.include_router(users_hierarchical.router)  # Usuários hierárquicos

# System optimization and monitoring
api_router.include_router(system_optimization.router)  # Otimização e monitoramento

# Todos os endpoints mock foram removidos - sistema deve usar dados reais do banco
