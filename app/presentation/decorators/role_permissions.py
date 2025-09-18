"""
Role-based Permission Decorators
Decorators que verificam permissões baseadas em perfis e permissões específicas
"""

from functools import wraps
from typing import Any, Optional

import structlog
from fastapi import Depends, HTTPException
from sqlalchemy import text

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User

logger = structlog.get_logger()


def require_role_permission(permission: str, context_type: str = "establishment"):
    """
    Decorator que verifica se usuário tem permissão específica através de seus perfis

    Args:
        permission: Nome da permissão (ex: "companies.view", "users.create")
        context_type: Tipo de contexto ("system", "company", "establishment")

    Usage:
        @require_role_permission("companies.view", "company")
        async def get_companies(): pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db=Depends(get_db),
            **kwargs,
        ):
            # Verificar se usuário tem a permissão específica através de seus perfis
            query = text(
                """
                SELECT COUNT(*) > 0 as has_permission
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                JOIN master.role_permissions rp ON r.id = rp.role_id
                JOIN master.permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = :user_id
                  AND ur.context_type = :context_type
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND r.is_active = true
                  AND p.is_active = true
                  AND p.name = :permission
            """
            )

            result = await db.execute(
                query,
                {
                    "user_id": current_user.id,
                    "context_type": context_type,
                    "permission": permission,
                },
            )

            has_permission = result.scalar() or False

            if not has_permission:
                await logger.awarning(
                    "permission_denied",
                    user_id=current_user.id,
                    permission=permission,
                    context_type=context_type,
                    endpoint=func.__name__,
                )

                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "message": f"Missing permission: {permission}",
                        "required_permission": permission,
                        "context_type": context_type,
                    },
                )

            await logger.ainfo(
                "permission_granted",
                user_id=current_user.id,
                permission=permission,
                context_type=context_type,
                endpoint=func.__name__,
            )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


def require_role_level_or_permission(
    min_level: int, permission: str, context_type: str = "establishment"
):
    """
    Decorator que verifica nível de role OU permissão específica
    (OR logic - se tiver nível suficiente OU permissão específica, permite acesso)

    Args:
        min_level: Nível mínimo necessário
        permission: Nome da permissão alternativa
        context_type: Tipo de contexto

    Usage:
        @require_role_level_or_permission(80, "companies.view", "company")
        async def get_companies(): pass
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db=Depends(get_db),
            **kwargs,
        ):
            # Verificar nível de role
            level_query = text(
                """
                SELECT MAX(r.level) as max_level
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id
                  AND ur.context_type = :context_type
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND r.is_active = true
            """
            )

            level_result = await db.execute(
                level_query, {"user_id": current_user.id, "context_type": context_type}
            )

            max_level = level_result.scalar() or 0

            # Verificar permissão específica
            perm_query = text(
                """
                SELECT COUNT(*) > 0 as has_permission
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                JOIN master.role_permissions rp ON r.id = rp.role_id
                JOIN master.permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = :user_id
                  AND ur.context_type = :context_type
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND r.is_active = true
                  AND p.is_active = true
                  AND p.name = :permission
            """
            )

            perm_result = await db.execute(
                perm_query,
                {
                    "user_id": current_user.id,
                    "context_type": context_type,
                    "permission": permission,
                },
            )

            has_permission = perm_result.scalar() or False

            # Permitir se tiver nível suficiente OU permissão específica
            has_access = (max_level >= min_level) or has_permission

            if not has_access:
                await logger.awarning(
                    "access_denied_level_or_permission",
                    user_id=current_user.id,
                    max_level=max_level,
                    required_level=min_level,
                    permission=permission,
                    has_permission=has_permission,
                    context_type=context_type,
                    endpoint=func.__name__,
                )

                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "access_denied",
                        "message": f"Required level {min_level} OR permission '{permission}'",
                        "required_level": min_level,
                        "required_permission": permission,
                        "current_level": max_level,
                        "has_permission": has_permission,
                        "context_type": context_type,
                    },
                )

            await logger.ainfo(
                "access_granted_level_or_permission",
                user_id=current_user.id,
                access_reason="level" if max_level >= min_level else "permission",
                level=max_level,
                permission=permission,
                context_type=context_type,
                endpoint=func.__name__,
            )

            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator
