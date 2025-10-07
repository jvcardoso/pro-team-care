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
