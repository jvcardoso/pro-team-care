from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.presentation.decorators.simple_permissions import require_permission

router = APIRouter()


class NotificationResponse(BaseModel):
    """Notification response model"""

    id: int
    title: str
    message: str
    type: str = "info"
    is_read: bool = False
    created_at: str


class NotificationListResponse(BaseModel):
    """Notification list response"""

    notifications: List[NotificationResponse] = []
    total: int = 0
    page: int = 1
    per_page: int = 20









