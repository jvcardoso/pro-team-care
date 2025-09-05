"""
Debug Menus API - Endpoint público temporário para debugging mobile
"""

from fastapi import APIRouter
import time

# Router independente SEM AUTENTICAÇÃO
debug_router = APIRouter(prefix="/debug", tags=["Debug"])

@debug_router.get("/menus-public")
async def get_debug_menus_public_simple():
    """
    Endpoint público temporário para debug do menu mobile
    SEM AUTENTICAÇÃO - SEM DEPENDÊNCIAS
    """
    
    return {
        "debug": True,
        "message": "Endpoint debug funcionando",
        "tree": [
            {
                "id": 1,
                "name": "Dashboard (Debug)",
                "slug": "dashboard-debug",
                "url": "/admin",
                "icon": "LayoutDashboard",
                "level": 0,
                "sort_order": 1,
                "is_visible": True,
                "visible_in_menu": True,
                "children": []
            },
            {
                "id": 2,
                "name": "Empresas (Debug)",
                "slug": "empresas-debug",
                "url": "/admin/empresas", 
                "icon": "Building",
                "level": 0,
                "sort_order": 2,
                "is_visible": True,
                "visible_in_menu": True,
                "children": []
            },
            {
                "id": 3,
                "name": "Administração (Debug)",
                "slug": "admin-debug",
                "url": "#",
                "icon": "Settings",
                "level": 0,
                "sort_order": 3,
                "is_visible": True,
                "visible_in_menu": True,
                "children": [
                    {
                        "id": 31,
                        "name": "Usuários",
                        "slug": "usuarios-debug",
                        "url": "/admin/usuarios",
                        "icon": "Users",
                        "level": 1,
                        "sort_order": 1,
                        "is_visible": True,
                        "visible_in_menu": True,
                        "children": []
                    },
                    {
                        "id": 32,
                        "name": "Configurações",
                        "slug": "config-debug",
                        "url": "/admin/config",
                        "icon": "Settings",
                        "level": 1,
                        "sort_order": 2,
                        "is_visible": True,
                        "visible_in_menu": True,
                        "children": []
                    }
                ]
            }
        ],
        "total_menus": 3,
        "cache_hit": False,
        "endpoint": "debug-menus-public-simple",
        "timestamp": time.time(),
        "status": "working"
    }