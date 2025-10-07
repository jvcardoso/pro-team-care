from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.services.admin_dashboard_service import AdminDashboardService
from app.presentation.decorators.simple_permissions import require_permission

router = APIRouter()


class DashboardStats(BaseModel):
    """Dashboard statistics"""

    total_users: int = 0
    active_users: int = 0
    total_companies: int = 0
    total_establishments: int = 0


class UserDashboardResponse(BaseModel):
    """User dashboard response"""

    user_stats: Dict[str, Any] = {}
    recent_activities: List[Dict[str, Any]] = []
    generated_at: datetime


class EstablishmentDashboardResponse(BaseModel):
    """Establishment dashboard response"""

    establishment_stats: Dict[str, Any] = {}
    recent_activities: List[Dict[str, Any]] = []
    generated_at: datetime


@router.get("/admin")
@require_permission(permission="dashboard.admin", context_type="system")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Dashboard principal para administradores com dados reais"""
    service = AdminDashboardService(db)
    return await service.get_dashboard_metrics()


@router.get("/user", response_model=UserDashboardResponse)
@require_permission(permission="dashboard.user", context_type="establishment")
async def get_user_dashboard(current_user: User = Depends(get_current_user)):
    """Dashboard personalizado para usuários normais"""
    return UserDashboardResponse(
        user_stats={
            "last_login": "2025-01-01T10:00:00",
            "notifications_count": 3,
            "active_sessions": 1,
        },
        recent_activities=[
            {"action": "login", "timestamp": "2025-01-01T10:00:00"},
            {"action": "profile_updated", "timestamp": "2025-01-01T09:45:00"},
        ],
        generated_at=datetime.now(),
    )


@router.get(
    "/establishment/{establishment_id}", response_model=EstablishmentDashboardResponse
)
@require_permission(permission="dashboard.establishment", context_type="establishment")
async def get_establishment_dashboard(
    establishment_id: int, current_user: User = Depends(get_current_user)
):
    """Dashboard específico de estabelecimento"""
    return EstablishmentDashboardResponse(
        establishment_stats={
            "establishment_id": establishment_id,
            "total_clients": 50,
            "active_professionals": 10,
            "appointments_today": 15,
        },
        recent_activities=[
            {
                "action": "appointment_scheduled",
                "client": "Client #123",
                "timestamp": "2025-01-01T10:00:00",
            },
            {
                "action": "professional_added",
                "professional": "Dr. Smith",
                "timestamp": "2025-01-01T09:30:00",
            },
        ],
        generated_at=datetime.now(),
    )


@router.get("/metrics")
@require_permission(permission="dashboard.metrics", context_type="establishment")
async def get_dashboard_metrics(current_user: User = Depends(get_current_user)):
    """Métricas gerais do dashboard"""
    return {
        "system_health": "healthy",
        "active_connections": 50,
        "response_time": "4ms",
        "uptime": "99.9%",
    }


@router.get("/recent-activities")
@require_permission(permission="dashboard.activities", context_type="establishment")
async def get_recent_activities(current_user: User = Depends(get_current_user)):
    """Atividades recentes do sistema"""
    return {
        "activities": [
            {
                "action": "user_login",
                "user": "admin@example.com",
                "timestamp": "2025-01-01T10:00:00",
            },
            {
                "action": "data_export",
                "user": "manager@example.com",
                "timestamp": "2025-01-01T09:45:00",
            },
            {
                "action": "report_generated",
                "user": "analyst@example.com",
                "timestamp": "2025-01-01T09:30:00",
            },
        ]
    }
