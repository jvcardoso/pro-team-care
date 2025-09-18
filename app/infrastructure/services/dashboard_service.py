"""
Dashboard Service - Analytics e métricas para painéis administrativos
Integra com views e functions PostgreSQL para dados em tempo real
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, func, select, text

from app.infrastructure.orm.models import Client, Establishments, Professional, User
from app.infrastructure.services.security_service import SecurityService

logger = structlog.get_logger()


@dataclass
class DashboardMetric:
    """Métrica do dashboard"""

    key: str
    value: int | float
    label: str
    description: str
    trend: Optional[str] = None  # "up", "down", "stable"
    trend_value: Optional[float] = None
    format_type: str = "number"  # "number", "currency", "percentage"


@dataclass
class ChartData:
    """Dados para gráficos"""

    labels: List[str]
    datasets: List[Dict[str, Any]]
    type: str  # "line", "bar", "pie", "doughnut"
    title: str
    description: Optional[str] = None


@dataclass
class DashboardAlert:
    """Alerta do dashboard"""

    id: str
    type: str  # "warning", "error", "info", "success"
    title: str
    message: str
    timestamp: datetime
    action_text: Optional[str] = None
    action_url: Optional[str] = None
    is_dismissible: bool = True


class DashboardService:
    """
    Serviço de dashboard com analytics e métricas do sistema
    """

    def __init__(self, session, security_service: SecurityService):
        self.session = session
        self.security_service = security_service

    async def get_admin_dashboard(
        self, user_id: int, date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Dashboard principal para administradores
        """
        try:
            # Verificar permissões
            if not await self.security_service.check_user_permission(
                user_id=user_id, permission="dashboard.admin"
            ):
                raise PermissionError("Acesso negado ao dashboard administrativo")

            # Definir período padrão (últimos 30 dias)
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            # Buscar métricas principais
            metrics = await self._get_admin_metrics(date_range)

            # Buscar dados para gráficos
            charts = await self._get_admin_charts(date_range)

            # Buscar alertas
            alerts = await self._get_system_alerts(user_id)

            # Buscar atividades recentes
            recent_activities = await self._get_recent_activities(limit=10)

            # Buscar estatísticas por estabelecimento
            establishment_stats = await self._get_establishment_stats()

            dashboard = {
                "metrics": metrics,
                "charts": charts,
                "alerts": alerts,
                "recent_activities": recent_activities,
                "establishment_stats": establishment_stats,
                "date_range": {
                    "start": date_range[0].isoformat(),
                    "end": date_range[1].isoformat(),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

            await logger.ainfo(
                "admin_dashboard_generated",
                user_id=user_id,
                metrics_count=len(metrics),
                charts_count=len(charts),
                alerts_count=len(alerts),
            )

            return dashboard

        except Exception as e:
            await logger.aerror("admin_dashboard_failed", user_id=user_id, error=str(e))
            raise

    async def get_user_dashboard(
        self, user_id: int, establishment_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Dashboard personalizado para usuários normais
        """
        try:
            # Buscar perfil do usuário
            user_profiles = await self.security_service.get_available_profiles(user_id)
            current_profile = user_profiles[0] if user_profiles else None

            if not establishment_id and current_profile:
                establishment_id = current_profile.get("establishment_id")

            # Métricas específicas do usuário
            user_metrics = await self._get_user_metrics(user_id, establishment_id)

            # Atividades do usuário
            user_activities = await self._get_user_activities(user_id, limit=5)

            # Tarefas pendentes
            pending_tasks = await self._get_user_pending_tasks(user_id)

            # Notificações
            notifications = await self._get_user_notifications(user_id, limit=5)

            dashboard = {
                "user_metrics": user_metrics,
                "activities": user_activities,
                "pending_tasks": pending_tasks,
                "notifications": notifications,
                "profile": current_profile,
                "generated_at": datetime.utcnow().isoformat(),
            }

            await logger.ainfo(
                "user_dashboard_generated",
                user_id=user_id,
                establishment_id=establishment_id,
            )

            return dashboard

        except Exception as e:
            await logger.aerror("user_dashboard_failed", user_id=user_id, error=str(e))
            raise

    async def get_establishment_dashboard(
        self, user_id: int, establishment_id: int
    ) -> Dict[str, Any]:
        """
        Dashboard específico de estabelecimento
        """
        try:
            # Verificar acesso ao estabelecimento
            can_access = await self.security_service.can_access_establishment_data(
                user_id=user_id, establishment_id=establishment_id
            )

            if not can_access:
                raise PermissionError("Acesso negado ao estabelecimento")

            # Métricas do estabelecimento
            metrics = await self._get_establishment_metrics(establishment_id)

            # Profissionais ativos
            professionals = await self._get_establishment_professionals(
                establishment_id
            )

            # Clientes recentes
            recent_clients = await self._get_establishment_recent_clients(
                establishment_id
            )

            # Estatísticas de atendimento (preparado para futuras implementações)
            service_stats = await self._get_establishment_service_stats(
                establishment_id
            )

            dashboard = {
                "establishment_id": establishment_id,
                "metrics": metrics,
                "professionals": professionals,
                "recent_clients": recent_clients,
                "service_stats": service_stats,
                "generated_at": datetime.utcnow().isoformat(),
            }

            await logger.ainfo(
                "establishment_dashboard_generated",
                user_id=user_id,
                establishment_id=establishment_id,
            )

            return dashboard

        except Exception as e:
            await logger.aerror(
                "establishment_dashboard_failed",
                user_id=user_id,
                establishment_id=establishment_id,
                error=str(e),
            )
            raise

    async def _get_admin_metrics(
        self, date_range: Tuple[datetime, datetime]
    ) -> List[DashboardMetric]:
        """
        Métricas administrativas principais
        """
        metrics = []

        try:
            # Total de usuários
            total_users = await self.session.execute(
                select(func.count(User.id)).where(User.deleted_at.is_(None))
            )
            total_users = total_users.scalar() or 0

            # Usuários ativos
            active_users = await self.session.execute(
                select(func.count(User.id)).where(
                    and_(User.is_active == True, User.deleted_at.is_(None))
                )
            )
            active_users = active_users.scalar() or 0

            # Total de profissionais
            total_professionals = await self.session.execute(
                select(func.count(Professional.id)).where(
                    Professional.deleted_at.is_(None)
                )
            )
            total_professionals = total_professionals.scalar() or 0

            # Total de clientes
            total_clients = await self.session.execute(
                select(func.count(Client.id)).where(Client.deleted_at.is_(None))
            )
            total_clients = total_clients.scalar() or 0

            # Total de estabelecimentos
            total_establishments = await self.session.execute(
                select(func.count(Establishments.id)).where(
                    Establishments.deleted_at.is_(None)
                )
            )
            total_establishments = total_establishments.scalar() or 0

            metrics.extend(
                [
                    DashboardMetric(
                        key="total_users",
                        value=total_users,
                        label="Total de Usuários",
                        description="Usuários cadastrados no sistema",
                    ),
                    DashboardMetric(
                        key="active_users",
                        value=active_users,
                        label="Usuários Ativos",
                        description="Usuários com status ativo",
                    ),
                    DashboardMetric(
                        key="total_professionals",
                        value=total_professionals,
                        label="Profissionais",
                        description="Profissionais cadastrados",
                    ),
                    DashboardMetric(
                        key="total_clients",
                        value=total_clients,
                        label="Clientes",
                        description="Clientes cadastrados",
                    ),
                    DashboardMetric(
                        key="total_establishments",
                        value=total_establishments,
                        label="Estabelecimentos",
                        description="Estabelecimentos ativos",
                    ),
                ]
            )

        except Exception as e:
            await logger.aerror("admin_metrics_failed", error=str(e))

        return metrics

    async def _get_admin_charts(
        self, date_range: Tuple[datetime, datetime]
    ) -> List[ChartData]:
        """
        Dados para gráficos administrativos
        """
        charts = []

        try:
            # Gráfico de usuários por mês (últimos 6 meses)
            user_growth_query = text(
                """
                SELECT
                    TO_CHAR(created_at, 'YYYY-MM') as month,
                    COUNT(*) as count
                FROM master.users
                WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
                  AND deleted_at IS NULL
                GROUP BY TO_CHAR(created_at, 'YYYY-MM')
                ORDER BY month
            """
            )

            result = await self.session.execute(user_growth_query)
            user_growth_data = result.fetchall()

            if user_growth_data:
                charts.append(
                    ChartData(
                        labels=[row.month for row in user_growth_data],
                        datasets=[
                            {
                                "label": "Novos Usuários",
                                "data": [row.count for row in user_growth_data],
                                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                                "borderColor": "rgba(54, 162, 235, 1)",
                                "borderWidth": 1,
                            }
                        ],
                        type="line",
                        title="Crescimento de Usuários",
                        description="Novos usuários por mês",
                    )
                )

            # Gráfico de distribuição por roles
            roles_query = text(
                """
                SELECT
                    r.display_name,
                    COUNT(ur.user_id) as count
                FROM master.roles r
                LEFT JOIN master.user_roles ur ON r.id = ur.role_id
                WHERE r.is_active = true
                GROUP BY r.id, r.display_name
                ORDER BY count DESC
            """
            )

            result = await self.session.execute(roles_query)
            roles_data = result.fetchall()

            if roles_data:
                charts.append(
                    ChartData(
                        labels=[row.display_name for row in roles_data],
                        datasets=[
                            {
                                "label": "Usuários por Role",
                                "data": [row.count for row in roles_data],
                                "backgroundColor": [
                                    "rgba(255, 99, 132, 0.2)",
                                    "rgba(54, 162, 235, 0.2)",
                                    "rgba(255, 205, 86, 0.2)",
                                    "rgba(75, 192, 192, 0.2)",
                                    "rgba(153, 102, 255, 0.2)",
                                ],
                            }
                        ],
                        type="doughnut",
                        title="Distribuição por Roles",
                        description="Usuários distribuídos por função",
                    )
                )

        except Exception as e:
            await logger.aerror("admin_charts_failed", error=str(e))

        return charts

    async def _get_system_alerts(self, user_id: int) -> List[DashboardAlert]:
        """
        Alertas do sistema para administradores
        """
        alerts = []

        try:
            # Verificar usuários sem login recente
            inactive_users_query = text(
                """
                SELECT COUNT(*)
                FROM master.users
                WHERE last_login_at < CURRENT_DATE - INTERVAL '30 days'
                  OR last_login_at IS NULL
                  AND is_active = true
                  AND deleted_at IS NULL
            """
            )

            result = await self.session.execute(inactive_users_query)
            inactive_count = result.scalar() or 0

            if inactive_count > 0:
                alerts.append(
                    DashboardAlert(
                        id="inactive_users",
                        type="warning",
                        title="Usuários Inativos",
                        message=f"{inactive_count} usuários não fazem login há mais de 30 dias",
                        action_text="Ver Usuários",
                        action_url="/admin/users?filter=inactive",
                        timestamp=datetime.utcnow(),
                    )
                )

            # Verificar estabelecimentos sem profissionais
            empty_establishments_query = text(
                """
                SELECT COUNT(*)
                FROM master.establishments e
                WHERE e.deleted_at IS NULL
                  AND e.is_active = true
                  AND NOT EXISTS (
                    SELECT 1 FROM master.professionals p
                    WHERE p.establishment_id = e.id
                      AND p.deleted_at IS NULL
                      AND p.status = 'ACTIVE'
                  )
            """
            )

            result = await self.session.execute(empty_establishments_query)
            empty_count = result.scalar() or 0

            if empty_count > 0:
                alerts.append(
                    DashboardAlert(
                        id="empty_establishments",
                        type="info",
                        title="Estabelecimentos sem Profissionais",
                        message=f"{empty_count} estabelecimentos não possuem profissionais cadastrados",
                        action_text="Ver Estabelecimentos",
                        action_url="/admin/establishments?filter=empty",
                        timestamp=datetime.utcnow(),
                    )
                )

        except Exception as e:
            await logger.aerror("system_alerts_failed", error=str(e))

        return alerts

    async def _get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Atividades recentes do sistema
        """
        try:
            # Por enquanto, usar dados de criação de usuários como atividades
            query = text(
                """
                SELECT
                    'user_created' as activity_type,
                    u.email_address as description,
                    u.created_at as timestamp,
                    p.name as user_name
                FROM master.users u
                JOIN master.people p ON u.person_id = p.id
                WHERE u.deleted_at IS NULL
                ORDER BY u.created_at DESC
                LIMIT :limit
            """
            )

            result = await self.session.execute(query, {"limit": limit})
            activities = []

            for row in result.fetchall():
                activities.append(
                    {
                        "type": row.activity_type,
                        "description": f"Usuário {row.user_name} foi criado",
                        "timestamp": row.timestamp.isoformat(),
                        "details": {"email": row.description},
                    }
                )

            return activities

        except Exception as e:
            await logger.aerror("recent_activities_failed", error=str(e))
            return []

    async def _get_establishment_stats(self) -> List[Dict[str, Any]]:
        """
        Estatísticas por estabelecimento
        """
        try:
            query = text(
                """
                SELECT
                    e.id,
                    p.name as establishment_name,
                    e.code as establishment_code,
                    e.type as establishment_type,
                    COUNT(DISTINCT prof.id) as professionals_count,
                    COUNT(DISTINCT cl.id) as clients_count
                FROM master.establishments e
                JOIN master.people p ON e.person_id = p.id
                LEFT JOIN master.professionals prof ON prof.establishment_id = e.id
                  AND prof.deleted_at IS NULL AND prof.status = 'ACTIVE'
                LEFT JOIN master.clients cl ON cl.establishment_id = e.id
                  AND cl.deleted_at IS NULL AND cl.status = 'ACTIVE'
                WHERE e.deleted_at IS NULL AND e.is_active = true
                GROUP BY e.id, p.name, e.code, e.type
                ORDER BY p.name
            """
            )

            result = await self.session.execute(query)
            stats = []

            for row in result.fetchall():
                stats.append(
                    {
                        "id": row.id,
                        "name": row.establishment_name,
                        "code": row.establishment_code,
                        "type": row.establishment_type,
                        "professionals_count": row.professionals_count,
                        "clients_count": row.clients_count,
                    }
                )

            return stats

        except Exception as e:
            await logger.aerror("establishment_stats_failed", error=str(e))
            return []

    # Métodos auxiliares para dashboards específicos
    async def _get_user_metrics(
        self, user_id: int, establishment_id: Optional[int]
    ) -> List[DashboardMetric]:
        """Métricas específicas do usuário"""
        # Implementação simplificada - pode ser expandida
        return [
            DashboardMetric(
                key="user_profile_completion",
                value=85,
                label="Perfil Completo",
                description="Percentual de completude do perfil",
                format_type="percentage",
            )
        ]

    async def _get_user_activities(
        self, user_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Atividades recentes do usuário"""
        return []  # Implementação futura

    async def _get_user_pending_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Tarefas pendentes do usuário"""
        return []  # Implementação futura

    async def _get_user_notifications(
        self, user_id: int, limit: int
    ) -> List[Dict[str, Any]]:
        """Notificações do usuário"""
        return []  # Implementação futura

    async def _get_establishment_metrics(
        self, establishment_id: int
    ) -> List[DashboardMetric]:
        """Métricas específicas do estabelecimento"""
        return []  # Implementação futura

    async def _get_establishment_professionals(
        self, establishment_id: int
    ) -> List[Dict[str, Any]]:
        """Profissionais do estabelecimento"""
        return []  # Implementação futura

    async def _get_establishment_recent_clients(
        self, establishment_id: int
    ) -> List[Dict[str, Any]]:
        """Clientes recentes do estabelecimento"""
        return []  # Implementação futura

    async def _get_establishment_service_stats(
        self, establishment_id: int
    ) -> Dict[str, Any]:
        """Estatísticas de atendimento do estabelecimento"""
        return {}  # Implementação futura


# Factory function para dependency injection
def get_dashboard_service(
    session, security_service: SecurityService
) -> DashboardService:
    """Factory function for DashboardService"""
    return DashboardService(session, security_service)
