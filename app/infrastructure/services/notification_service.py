"""
Notification Service - Sistema de notificações em tempo real
Integra com WebSockets, email, SMS e push notifications
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog
from sqlalchemy import text

from app.infrastructure.services.security_service import SecurityService

logger = structlog.get_logger()


class NotificationType(Enum):
    """Tipos de notificação"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"
    USER_ACTION = "user_action"
    APPOINTMENT = "appointment"
    PAYMENT = "payment"
    SECURITY = "security"


class NotificationChannel(Enum):
    """Canais de entrega"""

    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"


@dataclass
class NotificationTemplate:
    """Template de notificação"""

    id: str
    name: str
    type: NotificationType
    title_template: str
    message_template: str
    channels: List[NotificationChannel]
    is_active: bool
    variables: List[str]


@dataclass
class Notification:
    """Notificação individual"""

    id: int
    user_id: int
    template_id: str
    type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    channels: List[NotificationChannel]
    is_read: bool
    is_sent: bool
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    priority: int  # 1=baixa, 5=alta


@dataclass
class NotificationPreferences:
    """Preferências de notificação do usuário"""

    user_id: int
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    quiet_hours_start: Optional[str]  # HH:MM
    quiet_hours_end: Optional[str]  # HH:MM
    categories: Dict[str, bool]  # categoria -> habilitado


class NotificationService:
    """
    Serviço de notificações com múltiplos canais e templates
    """

    def __init__(self, session, security_service: SecurityService):
        self.session = session
        self.security_service = security_service
        self._websocket_connections: Set[Any] = set()  # WebSocket connections

    async def create_notification(
        self,
        user_id: int,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        priority: int = 3,
        expires_in_hours: Optional[int] = 24,
        custom_channels: Optional[List[NotificationChannel]] = None,
    ) -> int:
        """
        Cria nova notificação baseada em template
        """
        try:
            # Buscar template
            template = await self._get_notification_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} não encontrado")

            # Verificar preferências do usuário
            preferences = await self._get_user_preferences(user_id)

            # Processar template com variáveis
            title = self._process_template(template.title_template, variables or {})
            message = self._process_template(template.message_template, variables or {})

            # Determinar canais baseado em preferências
            channels = custom_channels or template.channels
            enabled_channels = self._filter_channels_by_preferences(
                channels, preferences
            )

            # Calcular expiração
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

            # Criar notificação no banco
            notification_id = await self._create_notification_record(
                user_id=user_id,
                template_id=template_id,
                type=template.type,
                title=title,
                message=message,
                data=variables,
                channels=enabled_channels,
                priority=priority,
                expires_at=expires_at,
            )

            # Enviar pelos canais habilitados
            await self._send_notification(notification_id, enabled_channels)

            await logger.ainfo(
                "notification_created",
                notification_id=notification_id,
                user_id=user_id,
                template_id=template_id,
                channels=[c.value for c in enabled_channels],
            )

            return notification_id

        except Exception as e:
            await logger.aerror(
                "notification_creation_failed",
                user_id=user_id,
                template_id=template_id,
                error=str(e),
            )
            raise

    async def create_bulk_notification(
        self,
        user_ids: List[int],
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        priority: int = 3,
    ) -> List[int]:
        """
        Cria notificação para múltiplos usuários
        """
        notification_ids = []

        for user_id in user_ids:
            try:
                notification_id = await self.create_notification(
                    user_id=user_id,
                    template_id=template_id,
                    variables=variables,
                    priority=priority,
                )
                notification_ids.append(notification_id)
            except Exception as e:
                await logger.aerror(
                    "bulk_notification_failed", user_id=user_id, error=str(e)
                )
                continue

        await logger.ainfo(
            "bulk_notification_created",
            total_users=len(user_ids),
            successful=len(notification_ids),
            template_id=template_id,
        )

        return notification_ids

    async def get_user_notifications(
        self, user_id: int, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> List[Notification]:
        """
        Busca notificações do usuário
        """
        try:
            query = text(
                """
                SELECT
                    id, user_id, template_id, type, title, message, data,
                    channels, is_read, is_sent, sent_at, read_at, expires_at,
                    created_at, priority
                FROM master.notifications
                WHERE user_id = :user_id
                  AND (expires_at IS NULL OR expires_at > NOW())
                  AND (:unread_only = false OR is_read = false)
                ORDER BY priority DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "unread_only": unread_only,
                    "limit": limit,
                    "offset": offset,
                },
            )

            notifications = []
            for row in result.fetchall():
                notifications.append(
                    Notification(
                        id=row.id,
                        user_id=row.user_id,
                        template_id=row.template_id,
                        type=NotificationType(row.type),
                        title=row.title,
                        message=row.message,
                        data=row.data,
                        channels=[NotificationChannel(c) for c in row.channels],
                        is_read=row.is_read,
                        is_sent=row.is_sent,
                        sent_at=row.sent_at,
                        read_at=row.read_at,
                        expires_at=row.expires_at,
                        created_at=row.created_at,
                        priority=row.priority,
                    )
                )

            return notifications

        except Exception as e:
            await logger.aerror(
                "get_notifications_failed", user_id=user_id, error=str(e)
            )
            return []

    async def mark_as_read(self, user_id: int, notification_ids: List[int]) -> int:
        """
        Marca notificações como lidas
        """
        try:
            query = text(
                """
                UPDATE master.notifications
                SET is_read = true, read_at = NOW()
                WHERE id = ANY(:notification_ids)
                  AND user_id = :user_id
                  AND is_read = false
            """
            )

            result = await self.session.execute(
                query, {"user_id": user_id, "notification_ids": notification_ids}
            )

            await self.session.commit()
            updated_count = result.rowcount

            await logger.ainfo(
                "notifications_marked_read", user_id=user_id, count=updated_count
            )

            return updated_count

        except Exception as e:
            await logger.aerror("mark_read_failed", user_id=user_id, error=str(e))
            return 0

    async def mark_all_as_read(self, user_id: int) -> int:
        """
        Marca todas as notificações como lidas
        """
        try:
            query = text(
                """
                UPDATE master.notifications
                SET is_read = true, read_at = NOW()
                WHERE user_id = :user_id AND is_read = false
            """
            )

            result = await self.session.execute(query, {"user_id": user_id})
            await self.session.commit()

            updated_count = result.rowcount

            await logger.ainfo(
                "all_notifications_marked_read", user_id=user_id, count=updated_count
            )

            return updated_count

        except Exception as e:
            await logger.aerror("mark_all_read_failed", user_id=user_id, error=str(e))
            return 0

    async def get_unread_count(self, user_id: int) -> int:
        """
        Conta notificações não lidas
        """
        try:
            query = text(
                """
                SELECT COUNT(*)
                FROM master.notifications
                WHERE user_id = :user_id
                  AND is_read = false
                  AND (expires_at IS NULL OR expires_at > NOW())
            """
            )

            result = await self.session.execute(query, {"user_id": user_id})
            count = result.scalar() or 0

            return count

        except Exception as e:
            await logger.aerror("unread_count_failed", user_id=user_id, error=str(e))
            return 0

    async def update_user_preferences(
        self, user_id: int, preferences: NotificationPreferences
    ) -> bool:
        """
        Atualiza preferências de notificação do usuário
        """
        try:
            query = text(
                """
                INSERT INTO master.notification_preferences
                (user_id, email_enabled, sms_enabled, push_enabled, in_app_enabled,
                 quiet_hours_start, quiet_hours_end, categories, updated_at)
                VALUES (:user_id, :email_enabled, :sms_enabled, :push_enabled,
                       :in_app_enabled, :quiet_hours_start, :quiet_hours_end,
                       :categories, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    email_enabled = :email_enabled,
                    sms_enabled = :sms_enabled,
                    push_enabled = :push_enabled,
                    in_app_enabled = :in_app_enabled,
                    quiet_hours_start = :quiet_hours_start,
                    quiet_hours_end = :quiet_hours_end,
                    categories = :categories,
                    updated_at = NOW()
            """
            )

            await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "email_enabled": preferences.email_enabled,
                    "sms_enabled": preferences.sms_enabled,
                    "push_enabled": preferences.push_enabled,
                    "in_app_enabled": preferences.in_app_enabled,
                    "quiet_hours_start": preferences.quiet_hours_start,
                    "quiet_hours_end": preferences.quiet_hours_end,
                    "categories": json.dumps(preferences.categories),
                },
            )

            await self.session.commit()

            await logger.ainfo("notification_preferences_updated", user_id=user_id)

            return True

        except Exception as e:
            await logger.aerror(
                "update_preferences_failed", user_id=user_id, error=str(e)
            )
            return False

    async def send_system_alert(
        self,
        title: str,
        message: str,
        alert_type: NotificationType = NotificationType.SYSTEM,
        target_roles: Optional[List[str]] = None,
        target_users: Optional[List[int]] = None,
    ) -> List[int]:
        """
        Envia alerta do sistema para grupos específicos
        """
        try:
            # Determinar usuários destinatários
            if target_users:
                user_ids = target_users
            elif target_roles:
                # Buscar usuários por roles
                user_ids = await self._get_users_by_roles(target_roles)
            else:
                # Enviar para todos os admins
                user_ids = await self._get_admin_users()

            # Criar template temporário
            template_id = (
                f"system_alert_{alert_type.value}_{datetime.utcnow().timestamp()}"
            )

            notification_ids = []
            for user_id in user_ids:
                notification_id = await self._create_notification_record(
                    user_id=user_id,
                    template_id=template_id,
                    type=alert_type,
                    title=title,
                    message=message,
                    data={"is_system_alert": True},
                    channels=[
                        NotificationChannel.IN_APP,
                        NotificationChannel.WEBSOCKET,
                    ],
                    priority=5,  # Alta prioridade para alertas do sistema
                )

                notification_ids.append(notification_id)

                # Enviar via WebSocket se disponível
                await self._send_websocket_notification(
                    user_id,
                    {
                        "id": notification_id,
                        "type": alert_type.value,
                        "title": title,
                        "message": message,
                        "priority": 5,
                    },
                )

            await logger.ainfo(
                "system_alert_sent",
                title=title,
                alert_type=alert_type.value,
                recipients=len(notification_ids),
            )

            return notification_ids

        except Exception as e:
            await logger.aerror("system_alert_failed", title=title, error=str(e))
            return []

    # Métodos auxiliares privados
    async def _get_notification_template(
        self, template_id: str
    ) -> Optional[NotificationTemplate]:
        """Busca template de notificação"""
        try:
            query = text(
                """
                SELECT id, name, type, title_template, message_template,
                       channels, is_active, variables
                FROM master.notification_templates
                WHERE id = :template_id AND is_active = true
            """
            )

            result = await self.session.execute(query, {"template_id": template_id})
            row = result.fetchone()

            if row:
                return NotificationTemplate(
                    id=row.id,
                    name=row.name,
                    type=NotificationType(row.type),
                    title_template=row.title_template,
                    message_template=row.message_template,
                    channels=[NotificationChannel(c) for c in row.channels],
                    is_active=row.is_active,
                    variables=row.variables or [],
                )

            return None

        except Exception as e:
            await logger.aerror(
                "get_template_failed", template_id=template_id, error=str(e)
            )
            return None

    async def _get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """Busca preferências do usuário ou retorna padrões"""
        try:
            query = text(
                """
                SELECT email_enabled, sms_enabled, push_enabled, in_app_enabled,
                       quiet_hours_start, quiet_hours_end, categories
                FROM master.notification_preferences
                WHERE user_id = :user_id
            """
            )

            result = await self.session.execute(query, {"user_id": user_id})
            row = result.fetchone()

            if row:
                return NotificationPreferences(
                    user_id=user_id,
                    email_enabled=row.email_enabled,
                    sms_enabled=row.sms_enabled,
                    push_enabled=row.push_enabled,
                    in_app_enabled=row.in_app_enabled,
                    quiet_hours_start=row.quiet_hours_start,
                    quiet_hours_end=row.quiet_hours_end,
                    categories=json.loads(row.categories) if row.categories else {},
                )

            # Retornar preferências padrão
            return NotificationPreferences(
                user_id=user_id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                in_app_enabled=True,
                quiet_hours_start=None,
                quiet_hours_end=None,
                categories={},
            )

        except Exception as e:
            await logger.aerror("get_preferences_failed", user_id=user_id, error=str(e))
            # Retornar padrões em caso de erro
            return NotificationPreferences(
                user_id=user_id,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                in_app_enabled=True,
                quiet_hours_start=None,
                quiet_hours_end=None,
                categories={},
            )

    def _process_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Processa template substituindo variáveis"""
        try:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                template = template.replace(placeholder, str(value))
            return template
        except Exception:
            return template

    def _filter_channels_by_preferences(
        self, channels: List[NotificationChannel], preferences: NotificationPreferences
    ) -> List[NotificationChannel]:
        """Filtra canais baseado nas preferências do usuário"""
        enabled_channels = []

        for channel in channels:
            if channel == NotificationChannel.EMAIL and preferences.email_enabled:
                enabled_channels.append(channel)
            elif channel == NotificationChannel.SMS and preferences.sms_enabled:
                enabled_channels.append(channel)
            elif channel == NotificationChannel.PUSH and preferences.push_enabled:
                enabled_channels.append(channel)
            elif channel == NotificationChannel.IN_APP and preferences.in_app_enabled:
                enabled_channels.append(channel)
            elif channel == NotificationChannel.WEBSOCKET:
                enabled_channels.append(channel)  # WebSocket sempre habilitado

        return enabled_channels

    async def _create_notification_record(
        self,
        user_id: int,
        template_id: str,
        type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]],
        channels: List[NotificationChannel],
        priority: int,
        expires_at: Optional[datetime] = None,
    ) -> int:
        """Cria registro da notificação no banco"""
        query = text(
            """
            INSERT INTO master.notifications
            (user_id, template_id, type, title, message, data, channels,
             priority, expires_at, created_at)
            VALUES (:user_id, :template_id, :type, :title, :message, :data,
                   :channels, :priority, :expires_at, NOW())
            RETURNING id
        """
        )

        result = await self.session.execute(
            query,
            {
                "user_id": user_id,
                "template_id": template_id,
                "type": type.value,
                "title": title,
                "message": message,
                "data": json.dumps(data) if data else None,
                "channels": [c.value for c in channels],
                "priority": priority,
                "expires_at": expires_at,
            },
        )

        await self.session.commit()
        notification_id = result.scalar()
        return notification_id

    async def _send_notification(
        self, notification_id: int, channels: List[NotificationChannel]
    ):
        """Envia notificação pelos canais especificados"""
        for channel in channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    # Já está salvo no banco
                    pass
                elif channel == NotificationChannel.WEBSOCKET:
                    await self._send_websocket_notification_by_id(notification_id)
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(notification_id)
                elif channel == NotificationChannel.SMS:
                    await self._send_sms_notification(notification_id)
                elif channel == NotificationChannel.PUSH:
                    await self._send_push_notification(notification_id)
            except Exception as e:
                await logger.aerror(
                    "notification_send_failed",
                    notification_id=notification_id,
                    channel=channel.value,
                    error=str(e),
                )

    async def _send_websocket_notification(self, user_id: int, data: Dict[str, Any]):
        """Envia notificação via WebSocket"""
        # Implementação simplificada - seria integrada com WebSocket manager real
        await logger.ainfo("websocket_notification_sent", user_id=user_id)

    async def _send_websocket_notification_by_id(self, notification_id: int):
        """Envia notificação via WebSocket usando ID"""
        # Implementação futura

    async def _send_email_notification(self, notification_id: int):
        """Envia notificação por email"""
        # Implementação futura - integração com serviço de email

    async def _send_sms_notification(self, notification_id: int):
        """Envia notificação por SMS"""
        # Implementação futura - integração com serviço de SMS

    async def _send_push_notification(self, notification_id: int):
        """Envia push notification"""
        # Implementação futura - integração com FCM/APNS

    async def _get_users_by_roles(self, roles: List[str]) -> List[int]:
        """Busca usuários por roles"""
        try:
            query = text(
                """
                SELECT DISTINCT u.id
                FROM master.users u
                JOIN master.user_roles ur ON u.id = ur.user_id
                JOIN master.roles r ON ur.role_id = r.id
                WHERE r.name = ANY(:roles)
                  AND u.is_active = true
                  AND u.deleted_at IS NULL
                  AND ur.status = 'ACTIVE'
            """
            )

            result = await self.session.execute(query, {"roles": roles})
            return [row.id for row in result.fetchall()]

        except Exception as e:
            await logger.aerror("get_users_by_roles_failed", error=str(e))
            return []

    async def _get_admin_users(self) -> List[int]:
        """Busca usuários administradores"""
        try:
            query = text(
                """
                SELECT id FROM master.users
                WHERE is_system_admin = true
                  AND is_active = true
                  AND deleted_at IS NULL
            """
            )

            result = await self.session.execute(query)
            return [row.id for row in result.fetchall()]

        except Exception as e:
            await logger.aerror("get_admin_users_failed", error=str(e))
            return []


# Factory function para dependency injection
def get_notification_service(
    session, security_service: SecurityService
) -> NotificationService:
    """Factory function for NotificationService"""
    return NotificationService(session, security_service)
