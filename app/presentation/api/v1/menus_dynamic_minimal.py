from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MenuItemResponse(BaseModel):
    """Minimal menu item response"""

    id: int
    name: str
    url: Optional[str] = None


@router.get("/user/{user_id}", response_model=List[MenuItemResponse])
async def get_user_menus_minimal(user_id: int):
    """Minimal menu endpoint for testing"""
    return [
        MenuItemResponse(id=1, name="Dashboard", url="/dashboard"),
        MenuItemResponse(id=2, name="Users", url="/users"),
    ]


@router.get("/tree", response_model=List[MenuItemResponse])
async def get_menu_tree_minimal():
    """Minimal menu tree for testing"""
    return [
        MenuItemResponse(id=1, name="Dashboard", url="/dashboard"),
        MenuItemResponse(id=2, name="Users", url="/users"),
    ]
