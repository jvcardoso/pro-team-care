"""
Sistema de Permissões Simples e Seguro
Implementação baseada no estudo de viabilidade

PRINCÍPIOS:
1. ❌ SEM LEVELS - Apenas permissões nomeadas
2. 🏦 DADOS DO BANCO - Zero fallbacks
3. 🔍 CONTROLE POR CONTEXT - System/Company/Establishment
4. 👑 SYSTEM ADMIN - Acesso irrestrito para is_system_admin = true
5. 🔒 ISOLAMENTO - Usuários normais só veem dados da própria empresa/estabelecimento
"""

from functools import wraps
from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db

logger = structlog.get_logger()


class SimplePermissionChecker:
    """
    Verificador de permissões simples e seguro
    SEM fallbacks, SEM levels, apenas permissões do banco
    """

    async def check_permission(
        self,
        user_id: int,
        permission: str,
        context_type: str,
        context_id: Optional[int] = None,
        is_system_admin: bool = False,
    ) -> bool:
        """
        Verificação ÚNICA de permissão via banco

        Args:
            user_id: ID do usuário
            permission: Nome da permissão (ex: "companies.view")
            context_type: Tipo do contexto ("system", "company", "establishment")
            context_id: ID do contexto (opcional)
            is_system_admin: Se é admin do sistema

        Returns:
            bool: True se tem permissão, False caso contrário
        """

        # 👑 SYSTEM ADMIN: Acesso irrestrito
        if is_system_admin:
            await logger.ainfo(
                "✅ System admin bypass - acesso total concedido",
                user_id=user_id,
                permission=permission,
                context_type=context_type,
            )
            return True

        # TEMPORARY: Allow all access for debugging
        """
        await logger.awarning(
            "TEMPORARY DEBUG: Allowing all access",
            user_id=user_id,
            permission=permission,
            context_type=context_type,
        )
        return True
        """
        # 🔍 VERIFICAÇÃO ÚNICA VIA BANCO - SEM FALLBACKS
        try:
            from sqlalchemy import text

            from app.infrastructure.database import async_session

            async with async_session() as db:
                # Query única e simples - SEM JOINs complexos
                if context_id is None:
                    # Contexto sem ID específico (ex: system level)
                    query = text(
                        """
                        SELECT COUNT(*) > 0 as has_permission
                        FROM master.user_roles ur
                        JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                        JOIN master.permissions p ON rp.permission_id = p.id
                        WHERE ur.user_id = :user_id
                          AND p.name = :permission
                          AND p.context_level = :context_type
                          AND ur.status = 'active'
                          AND ur.deleted_at IS NULL
                          AND p.is_active = true
                    """
                    )
                    params = {
                        "user_id": user_id,
                        "permission": permission,
                        "context_type": context_type,
                    }
                else:
                    # Contexto com ID específico (ex: company/establishment)
                    query = text(
                        """
                        SELECT COUNT(*) > 0 as has_permission
                        FROM master.user_roles ur
                        JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                        JOIN master.permissions p ON rp.permission_id = p.id
                        WHERE ur.user_id = :user_id
                          AND p.name = :permission
                          AND p.context_level = :context_type
                          AND ur.context_id = :context_id
                          AND ur.status = 'active'
                          AND ur.deleted_at IS NULL
                          AND p.is_active = true
                    """
                    )
                    params = {
                        "user_id": user_id,
                        "permission": permission,
                        "context_type": context_type,
                        "context_id": context_id,
                    }

                result = await db.execute(query, params)
                has_permission = result.scalar() or False

                if has_permission:
                    await logger.ainfo(
                        "✅ Permissão concedida via banco",
                        user_id=user_id,
                        permission=permission,
                        context_type=context_type,
                        context_id=context_id,
                    )
                else:
                    await logger.awarning(
                        "❌ Permissão negada - sem permissão no banco",
                        user_id=user_id,
                        permission=permission,
                        context_type=context_type,
                        context_id=context_id,
                    )

                return has_permission

        except Exception as e:
            await logger.aerror(
                "🚨 Erro na verificação de permissão - acesso negado por segurança",
                user_id=user_id,
                permission=permission,
                error=str(e),
            )
            # SEGURANÇA: Em caso de erro, NEGAR acesso
            return False


# Instância global do verificador
permission_checker = SimplePermissionChecker()


def require_permission(
    permission: str,
    context_type: str = "establishment",
    get_context_id_from_kwargs: Optional[str] = None,
):
    """
    Decorator SIMPLES para verificação de permissões

    Args:
        permission: Nome da permissão (ex: "companies.view")
        context_type: Tipo do contexto ("system", "company", "establishment")
        get_context_id_from_kwargs: Nome do parâmetro que contém o context_id

    Examples:
        @require_permission("companies.view", context_type="system")
        async def get_companies(): pass

        @require_permission("establishments.view", context_type="company", get_context_id_from_kwargs="company_id")
        async def get_establishments(company_id: int): pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            **kwargs,
        ):
            # Determinar context_id se especificado
            context_id = None
            if get_context_id_from_kwargs and get_context_id_from_kwargs in kwargs:
                context_id = kwargs[get_context_id_from_kwargs]
            elif context_type == "company" and hasattr(current_user, "company_id"):
                context_id = current_user.company_id
            elif context_type == "establishment" and hasattr(
                current_user, "current_establishment_id"
            ):
                context_id = getattr(current_user, "current_establishment_id", None)

            # Verificação ÚNICA de permissão
            has_permission = await permission_checker.check_permission(
                user_id=current_user.id,
                permission=permission,
                context_type=context_type,
                context_id=context_id,
                is_system_admin=getattr(current_user, "is_system_admin", False),
            )

            if not has_permission:
                error_detail = {
                    "error": "permission_denied",
                    "message": f"Required permission: {permission}",
                    "required_permission": permission,
                    "context_type": context_type,
                    "context_id": context_id,
                    "user_id": current_user.id,
                }

                await logger.awarning(
                    "🚫 Access denied - permission required",
                    endpoint=func.__name__,
                    **error_detail,
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=error_detail
                )

            # ✅ Permissão concedida - executar função
            await logger.ainfo(
                "✅ Access granted",
                user_id=current_user.id,
                permission=permission,
                endpoint=func.__name__,
                context_type=context_type,
                context_id=context_id,
            )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_system_admin():
    """
    Decorator que requer privilégios de system admin
    Equivale a: @require_permission("system.admin", context_type="system")
    """
    return require_permission("system.admin", context_type="system")


def require_company_access(permission: str):
    """
    Decorator para permissões no nível da empresa
    Context_id será automaticamente o company_id do usuário
    """
    return require_permission(permission, context_type="company")


def require_establishment_access(permission: str):
    """
    Decorator para permissões no nível do estabelecimento
    Context_id será automaticamente o establishment_id do usuário
    """
    return require_permission(permission, context_type="establishment")


# Decorators específicos para uso comum
def require_companies_view():
    """Ver empresas - System level"""
    return require_permission("companies.view", context_type="system")


def require_companies_create():
    """Criar empresas - System level"""
    return require_permission("companies.create", context_type="system")


def require_establishments_view():
    """Ver estabelecimentos - Company level"""
    return require_permission("establishments.view", context_type="company")


def require_establishments_create():
    """Criar estabelecimentos - Company level"""
    return require_permission("establishments.create", context_type="company")


def require_users_view():
    """Ver usuários - Company level"""
    return require_permission("users.view", context_type="company")


def require_patients_view():
    """Ver pacientes - Establishment level"""
    return require_permission("patients.view", context_type="establishment")


def require_professionals_view():
    """Ver profissionais - Establishment level"""
    return require_permission("professionals.view", context_type="establishment")


# Funções utilitárias para verificação manual
async def check_user_permission_simple(
    user_id: int,
    permission: str,
    context_type: str = "establishment",
    context_id: Optional[int] = None,
    is_system_admin: bool = False,
) -> bool:
    """
    Verificação manual de permissão
    Útil para lógica condicional dentro de funções
    """
    return await permission_checker.check_permission(
        user_id=user_id,
        permission=permission,
        context_type=context_type,
        context_id=context_id,
        is_system_admin=is_system_admin,
    )
