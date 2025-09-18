"""
Security Service - Integração com Functions PostgreSQL de Segurança
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog
from fastapi import Depends
from sqlalchemy import text

from app.infrastructure.database import get_db

logger = structlog.get_logger()


@dataclass
class AccessibleUser:
    """Dados de usuário acessível hierarquicamente"""

    user_id: int
    email: str
    person_name: str
    company_id: Optional[int]
    establishment_id: Optional[int]
    role_level: int
    can_manage: bool


@dataclass
class SessionContext:
    """Contexto de sessão validado"""

    is_valid: bool
    effective_user_id: int
    current_role_id: Optional[int]
    context_type: str
    context_id: Optional[int]
    can_impersonate: bool


class SecurityService:
    """
    Serviço de segurança que integra com functions PostgreSQL
    Implementa as functions críticas do Sprint 1
    """

    def __init__(self, session):
        self.session = session

    async def check_user_permission(
        self,
        user_id: int,
        permission: str,
        context_type: str = "establishment",
        context_id: Optional[int] = None,
    ) -> bool:
        """
        Verifica se usuário possui permissão específica
        Function: check_user_permission
        """
        try:
            query = text(
                """
                SELECT master.check_user_permission_v2(
                    :user_id, :permission, :context_type, :context_id
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "permission": permission,
                    "context_type": context_type,
                    "context_id": context_id,
                },
            )

            has_permission = result.scalar() or False

            await logger.ainfo(
                "permission_check",
                user_id=user_id,
                permission=permission,
                context_type=context_type,
                context_id=context_id,
                result=has_permission,
            )

            return has_permission

        except Exception as e:
            await logger.aerror(
                "permission_check_failed",
                user_id=user_id,
                permission=permission,
                error=str(e),
            )
            return False

    async def can_access_user_data(
        self, requesting_user_id: int, target_user_id: int
    ) -> bool:
        """
        Verifica se usuário pode acessar dados de outro usuário (hierarquia)
        Function: can_access_user_data
        """
        try:
            query = text(
                """
                SELECT master.can_access_user_data(:requesting_user_id, :target_user_id)
            """
            )

            result = await self.session.execute(
                query,
                {
                    "requesting_user_id": requesting_user_id,
                    "target_user_id": target_user_id,
                },
            )

            can_access = result.scalar() or False

            await logger.ainfo(
                "user_data_access_check",
                requesting_user_id=requesting_user_id,
                target_user_id=target_user_id,
                result=can_access,
            )

            return can_access

        except Exception as e:
            await logger.aerror(
                "user_data_access_check_failed",
                requesting_user_id=requesting_user_id,
                target_user_id=target_user_id,
                error=str(e),
            )
            return False

    async def get_accessible_users_hierarchical(
        self, requesting_user_id: int
    ) -> List[AccessibleUser]:
        """
        Retorna usuários acessíveis hierarquicamente
        Function: get_accessible_users_hierarchical
        """
        try:
            query = text(
                """
                SELECT * FROM master.get_accessible_users_hierarchical(:user_id)
            """
            )

            result = await self.session.execute(query, {"user_id": requesting_user_id})

            users = []
            for row in result.fetchall():
                users.append(
                    AccessibleUser(
                        user_id=row.user_id,
                        email=row.email,
                        person_name=row.person_name,
                        company_id=row.company_id,
                        establishment_id=row.establishment_id,
                        role_level=row.role_level or 0,
                        can_manage=row.can_manage or False,
                    )
                )

            await logger.ainfo(
                "accessible_users_fetched",
                requesting_user_id=requesting_user_id,
                count=len(users),
            )

            return users

        except Exception as e:
            await logger.aerror(
                "accessible_users_fetch_failed",
                requesting_user_id=requesting_user_id,
                error=str(e),
            )
            return []

    async def validate_session_context(
        self, session_token: str, user_id: Optional[int] = None
    ) -> SessionContext:
        """
        Valida sessão e contexto do usuário
        Function: validate_session_context
        """
        try:
            query = text(
                """
                SELECT * FROM master.validate_session_context(:session_token, :user_id)
            """
            )

            result = await self.session.execute(
                query, {"session_token": session_token, "user_id": user_id}
            )

            row = result.fetchone()

            if row:
                context = SessionContext(
                    is_valid=row.is_valid or False,
                    effective_user_id=row.effective_user_id or 0,
                    current_role_id=row.current_role_id,
                    context_type=row.context_type or "establishment",
                    context_id=row.context_id,
                    can_impersonate=row.can_impersonate or False,
                )
            else:
                context = SessionContext(
                    is_valid=False,
                    effective_user_id=0,
                    current_role_id=None,
                    context_type="establishment",
                    context_id=None,
                    can_impersonate=False,
                )

            await logger.ainfo(
                "session_context_validated",
                session_token=session_token[:10] + "...",
                is_valid=context.is_valid,
                user_id=context.effective_user_id,
            )

            return context

        except Exception as e:
            await logger.aerror(
                "session_context_validation_failed",
                session_token=session_token[:10] + "...",
                error=str(e),
            )
            return SessionContext(
                is_valid=False,
                effective_user_id=0,
                current_role_id=None,
                context_type="establishment",
                context_id=None,
                can_impersonate=False,
            )

    async def switch_user_context(
        self,
        user_id: int,
        new_context_type: str,
        new_context_id: int,
        session_token: str,
    ) -> bool:
        """
        Troca contexto do usuário (empresa/estabelecimento)
        Function: switch_user_context
        """
        try:
            query = text(
                """
                SELECT master.switch_user_context(
                    :user_id, :new_context_type, :new_context_id, :session_token
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "new_context_type": new_context_type,
                    "new_context_id": new_context_id,
                    "session_token": session_token,
                },
            )

            success = result.scalar() or False

            await logger.ainfo(
                "context_switch",
                user_id=user_id,
                new_context_type=new_context_type,
                new_context_id=new_context_id,
                success=success,
            )

            return success

        except Exception as e:
            await logger.aerror(
                "context_switch_failed",
                user_id=user_id,
                new_context_type=new_context_type,
                new_context_id=new_context_id,
                error=str(e),
            )
            return False

    async def get_available_profiles(
        self,
        user_id: int,
        context_type: str = "establishment",
        context_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retorna perfis disponíveis para o usuário no contexto
        Function: get_available_profiles
        """
        try:
            query = text(
                """
                SELECT * FROM master.get_available_profiles(:user_id)
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                },
            )

            profiles = []
            for row in result.fetchall():
                profiles.append(
                    {
                        "role_id": row.role_id,
                        "role_name": row.role_name,
                        "role_display_name": row.role_display_name,
                        "role_level": row.role_level,
                        "can_assign": row.can_assign or False,
                        "context_type": row.context_type,
                        "context_id": row.context_id,
                    }
                )

            await logger.ainfo(
                "available_profiles_fetched",
                user_id=user_id,
                context_type=context_type,
                count=len(profiles),
            )

            return profiles

        except Exception as e:
            await logger.aerror(
                "available_profiles_fetch_failed",
                user_id=user_id,
                context_type=context_type,
                error=str(e),
            )
            return []

    async def log_user_data_access(
        self,
        accessed_by_user_id: int,
        accessed_user_id: int,
        view_name: str,
        access_type: str = "read",
        additional_data: Optional[Dict] = None,
    ) -> bool:
        """
        Registra acesso a dados de usuário (auditoria LGPD)
        Function: log_user_data_access
        """
        try:
            query = text(
                """
                SELECT master.log_user_data_access(
                    :accessed_by_user_id, :accessed_user_id, :view_name,
                    :access_type, :additional_data
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "accessed_by_user_id": accessed_by_user_id,
                    "accessed_user_id": accessed_user_id,
                    "view_name": view_name,
                    "access_type": access_type,
                    "additional_data": additional_data,
                },
            )

            logged = result.scalar() or False

            # Log estruturado (não aguardar)
            logger.info(
                "user_data_access_logged",
                accessed_by=accessed_by_user_id,
                accessed_user=accessed_user_id,
                view=view_name,
                type=access_type,
            )

            return logged

        except Exception as e:
            await logger.aerror(
                "user_data_access_log_failed",
                accessed_by=accessed_by_user_id,
                accessed_user=accessed_user_id,
                view=view_name,
                error=str(e),
            )
            return False

    async def get_user_permissions(
        self,
        user_id: int,
        context_type: str = "establishment",
        context_id: Optional[int] = None,
    ) -> List[str]:
        """
        Retorna lista de permissões ativas do usuário
        Function: get_user_permissions
        """
        try:
            query = text(
                """
                SELECT permission_name
                FROM master.get_user_permissions(:user_id, :context_type, :context_id)
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "context_type": context_type,
                    "context_id": context_id,
                },
            )

            permissions = [row.permission_name for row in result.fetchall()]

            await logger.ainfo(
                "user_permissions_fetched",
                user_id=user_id,
                context_type=context_type,
                context_id=context_id,
                count=len(permissions),
            )

            return permissions

        except Exception as e:
            await logger.aerror(
                "user_permissions_fetch_failed",
                user_id=user_id,
                context_type=context_type,
                context_id=context_id,
                error=str(e),
            )
            return []


# Função de conveniência para dependency injection
async def get_security_service(db=Depends(get_db)) -> SecurityService:
    """Factory function for SecurityService"""
    return SecurityService(db)
