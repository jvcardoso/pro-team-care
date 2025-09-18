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


@router.get("/", response_model=NotificationListResponse)
@require_permission(permission="notifications.view", context_type="establishment")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Lista notificações do usuário atual"""
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=1,
                title="Welcome",
                message="Welcome to the system",
                type="info",
                created_at="2025-01-01T00:00:00",
            )
        ],
        total=1,
        page=1,
        per_page=20,
    )


@router.get("/unread-count")
@require_permission(permission="notifications.view", context_type="establishment")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    """Conta notificações não lidas"""
    return {"count": 0}


@router.post("/mark-read")
@require_permission(permission="notifications.edit", context_type="establishment")
async def mark_notifications_read(current_user: User = Depends(get_current_user)):
    """Marca notificações como lidas"""
    return {"message": "Notifications marked as read", "updated_count": 0}


@router.post("/mark-all-read")
@require_permission(permission="notifications.edit", context_type="establishment")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Marca todas as notificações como lidas"""
    return {"message": "All notifications marked as read", "updated_count": 0}


@router.get("/preferences")
async def get_notification_preferences():
    """Preferências de notificação"""
    return {"email_notifications": True, "push_notifications": True}


@router.put("/preferences")
async def update_notification_preferences():
    """Atualiza preferências de notificação"""
    return {"message": "Preferences updated"}


@router.post("/create")
@require_permission(permission="notifications.create", context_type="establishment")
async def create_notification(current_user: User = Depends(get_current_user)):
    """Cria nova notificação (placeholder)"""
    return {"message": "Notification created", "id": 1}


@router.post("/bulk-create")
@require_permission(permission="notifications.create", context_type="company")
async def create_bulk_notification(current_user: User = Depends(get_current_user)):
    """Cria notificação em massa (placeholder)"""
    return {"message": "Bulk notifications created", "ids": [1, 2, 3]}


@router.post("/system-alert")
@require_permission(permission="system.admin", context_type="system")
async def send_system_alert(current_user: User = Depends(get_current_user)):
    """Envia alerta do sistema (placeholder)"""
    return {"message": "System alert sent"}
