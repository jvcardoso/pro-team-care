from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MenuItemResponse(BaseModel):
    """Response model for menu items"""

    id: int
    name: str
    slug: str
    url: Optional[str] = None
    level: int = 0
    sort_order: int = 0
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    is_visible: bool = True
    visible_in_menu: bool = True
    children: List["MenuItemResponse"] = []


@router.get("/user/{user_id}", response_model=List[MenuItemResponse])
async def get_user_menus(user_id: int):
    """Busca menus dinâmicos para um usuário específico"""
    return [
        MenuItemResponse(
            id=1,
            name="Dashboard",
            slug="dashboard",
            url="/dashboard",
            level=0,
            sort_order=1,
            icon="dashboard",
        ),
        MenuItemResponse(
            id=2,
            name="Users",
            slug="users",
            url="/users",
            level=0,
            sort_order=2,
            icon="users",
        ),
    ]


@router.get("/tree", response_model=List[MenuItemResponse])
async def get_menu_tree():
    """Busca árvore de menus dinâmica"""
    return [
        MenuItemResponse(
            id=1,
            name="Dashboard",
            slug="dashboard",
            url="/dashboard",
            level=0,
            sort_order=1,
            icon="dashboard",
        ),
        MenuItemResponse(
            id=2,
            name="Users",
            slug="users",
            url="/users",
            level=0,
            sort_order=2,
            icon="users",
        ),
    ]


@router.get("/contextual")
async def get_contextual_menu():
    """Menu contextual (placeholder)"""
    return {"message": "Contextual menu - coming soon"}


@router.get("/breadcrumb")
async def get_breadcrumb():
    """Breadcrumb (placeholder)"""
    return {"breadcrumb": [{"name": "Home", "url": "/"}]}


@router.get("/shortcuts")
async def get_user_shortcuts():
    """User shortcuts (placeholder)"""
    return {"shortcuts": []}


@router.post("/shortcuts")
async def add_user_shortcut():
    """Add shortcut (placeholder)"""
    return {"message": "Shortcut added"}


@router.delete("/shortcuts/{menu_id}")
async def remove_user_shortcut(menu_id: int):
    """Remove shortcut (placeholder)"""
    return {"message": f"Shortcut {menu_id} removed"}


@router.get("/user-permissions")
async def get_user_menu_permissions():
    """User menu permissions (placeholder)"""
    return {"permissions": ["menu.view"]}
