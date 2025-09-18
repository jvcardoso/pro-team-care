"""
Endpoints de Administração de Permissões - Fase 3
Permite gestão completa do sistema de permissões granulares
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.role_repository import (
    PermissionRepository,
    RoleRepository,
)
from app.presentation.decorators.simple_permissions import require_permission

logger = structlog.get_logger()

router = APIRouter()

# ==========================================
# SCHEMAS DE ADMINISTRAÇÃO
# ==========================================


class UserPermissionAssignment(BaseModel):
    """Atribuição de permissão a usuário"""

    user_id: int
    role_id: int
    context_type: str = "establishment"
    context_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class BulkPermissionOperation(BaseModel):
    """Operação em massa de permissões"""

    user_ids: List[int]
    role_id: int
    context_type: str = "establishment"
    context_id: Optional[int] = None
    operation: str  # "assign" or "revoke"


class PermissionAuditEntry(BaseModel):
    """Entrada de auditoria de permissões"""

    id: int
    user_id: int
    user_email: str
    action: str
    permission_name: Optional[str] = None
    role_name: Optional[str] = None
    context_type: str
    context_id: Optional[int] = None
    performed_by_user_id: int
    performed_by_email: str
    created_at: datetime
    details: Optional[Dict[str, Any]] = None


class SystemPermissionStats(BaseModel):
    """Estatísticas do sistema de permissões"""

    total_users: int
    users_with_granular_permissions: int
    total_permissions: int
    total_roles: int
    migration_coverage_percent: float
    most_used_permissions: List[Dict[str, Any]]
    permission_distribution: Dict[str, int]


# ==========================================
# ENDPOINTS DE GESTÃO DE PERMISSÕES
# ==========================================


@router.post(
    "/assign-user-role",
    summary="Atribuir role a usuário",
    description="Atribuir role granular a um usuário específico",
    tags=["Permissions Admin"],
)
@require_permission(permission="system.admin", context_type="system")
async def assign_user_role(
    assignment: UserPermissionAssignment,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Atribuir role granular a usuário:

    - **user_id**: ID do usuário
    - **role_id**: ID do role granular
    - **context_type**: Contexto (system, company, establishment)
    - **context_id**: ID do contexto (opcional para system)
    - **expires_at**: Data de expiração (opcional)
    """
    try:
        from sqlalchemy import text

        # Verificar se o usuário existe
        user_check = await db.execute(
            text(
                """
            SELECT id, email_address FROM master.users WHERE id = :user_id AND deleted_at IS NULL
        """
            ),
            {"user_id": assignment.user_id},
        )

        user = user_check.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se o role existe
        role_check = await db.execute(
            text(
                """
            SELECT id, name FROM master.roles WHERE id = :role_id AND is_active = true
        """
            ),
            {"role_id": assignment.role_id},
        )

        role = role_check.fetchone()
        if not role:
            raise HTTPException(status_code=404, detail="Role não encontrado")

        # Verificar se já existe atribuição ativa
        existing_check = await db.execute(
            text(
                """
            SELECT id FROM master.user_roles
            WHERE user_id = :user_id
            AND role_id = :role_id
            AND context_type = :context_type
            AND (:context_id IS NULL OR context_id = :context_id)
            AND status = 'active'
            AND deleted_at IS NULL
        """
            ),
            {
                "user_id": assignment.user_id,
                "role_id": assignment.role_id,
                "context_type": assignment.context_type,
                "context_id": assignment.context_id,
            },
        )

        if existing_check.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Usuário já possui este role no contexto especificado",
            )

        # Criar atribuição
        await db.execute(
            text(
                """
            INSERT INTO master.user_roles (
                user_id, role_id, context_type, context_id,
                status, assigned_by_user_id, assigned_at, expires_at,
                created_at, updated_at
            ) VALUES (
                :user_id, :role_id, :context_type, :context_id,
                'active', :assigned_by, NOW(), :expires_at,
                NOW(), NOW()
            )
        """
            ),
            {
                "user_id": assignment.user_id,
                "role_id": assignment.role_id,
                "context_type": assignment.context_type,
                "context_id": assignment.context_id,
                "assigned_by": current_user.id,
                "expires_at": assignment.expires_at,
            },
        )

        await db.commit()

        logger.info(
            "Role assigned to user",
            user_id=assignment.user_id,
            user_email=user.email_address,
            role_id=assignment.role_id,
            role_name=role.name,
            context=f"{assignment.context_type}:{assignment.context_id}",
            assigned_by=current_user.id,
        )

        return {
            "message": "Role atribuído com sucesso",
            "user_email": user.email_address,
            "role_name": role.name,
            "context": f"{assignment.context_type}:{assignment.context_id}",
        }

    except Exception as e:
        await db.rollback()
        logger.error("Error assigning role to user", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post(
    "/revoke-user-role",
    summary="Revogar role de usuário",
    description="Remover role granular de um usuário",
    tags=["Permissions Admin"],
)
@require_permission(permission="system.admin", context_type="system")
async def revoke_user_role(
    user_id: int,
    role_id: int,
    context_type: str = "establishment",
    context_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Revogar role de usuário:

    - **user_id**: ID do usuário
    - **role_id**: ID do role
    - **context_type**: Contexto
    - **context_id**: ID do contexto
    """
    try:
        from sqlalchemy import text

        # Atualizar user_role para inativo
        result = await db.execute(
            text(
                """
            UPDATE master.user_roles
            SET status = 'revoked',
                updated_at = NOW(),
                deleted_at = NOW()
            WHERE user_id = :user_id
            AND role_id = :role_id
            AND context_type = :context_type
            AND (:context_id IS NULL OR context_id = :context_id)
            AND status = 'active'
            AND deleted_at IS NULL
            RETURNING id
        """
            ),
            {
                "user_id": user_id,
                "role_id": role_id,
                "context_type": context_type,
                "context_id": context_id,
            },
        )

        if not result.fetchone():
            raise HTTPException(
                status_code=404, detail="Atribuição de role não encontrada"
            )

        await db.commit()

        logger.info(
            "Role revoked from user",
            user_id=user_id,
            role_id=role_id,
            context=f"{context_type}:{context_id}",
            revoked_by=current_user.id,
        )

        return {"message": "Role revogado com sucesso"}

    except Exception as e:
        await db.rollback()
        logger.error("Error revoking role from user", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get(
    "/user/{user_id}/permissions",
    response_model=List[Dict[str, Any]],
    summary="Listar permissões do usuário",
    description="Listar todas as permissões de um usuário em todos os contextos",
    tags=["Permissions Admin"],
)
@require_permission(permission="users.permissions", context_type="establishment")
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Listar todas as permissões de um usuário"""
    try:
        from sqlalchemy import text

        result = await db.execute(
            text(
                """
            SELECT
                ur.context_type,
                ur.context_id,
                r.name as role_name,
                r.display_name as role_display_name,
                p.name as permission_name,
                p.display_name as permission_display_name,
                p.description as permission_description,
                ur.status,
                ur.expires_at,
                ur.assigned_at
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            JOIN master.role_permissions rp ON r.id = rp.role_id
            JOIN master.permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = :user_id
            AND ur.status = 'active'
            AND ur.deleted_at IS NULL
            AND p.is_active = true
            ORDER BY ur.context_type, p.name
        """
            ),
            {"user_id": user_id},
        )

        permissions = []
        for row in result.fetchall():
            permissions.append(
                {
                    "context": f"{row.context_type}:{row.context_id}",
                    "role_name": row.role_name,
                    "role_display_name": row.role_display_name,
                    "permission_name": row.permission_name,
                    "permission_display_name": row.permission_display_name,
                    "permission_description": row.permission_description,
                    "status": row.status,
                    "expires_at": row.expires_at,
                    "assigned_at": row.assigned_at,
                }
            )

        return permissions

    except Exception as e:
        logger.error("Error getting user permissions", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get(
    "/system/stats",
    response_model=SystemPermissionStats,
    summary="Estatísticas do sistema de permissões",
    description="Obter estatísticas gerais do sistema de permissões",
    tags=["Permissions Admin"],
)
@require_permission(permission="system.admin", context_type="system")
async def get_system_permission_stats(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Estatísticas do sistema de permissões"""
    try:
        from sqlalchemy import text

        # Total de usuários
        result = await db.execute(
            text("SELECT COUNT(*) FROM master.users WHERE deleted_at IS NULL")
        )
        total_users = result.scalar()

        # Usuários com permissões granulares
        result = await db.execute(
            text(
                """
            SELECT COUNT(DISTINCT ur.user_id)
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            WHERE r.name LIKE 'granular_%'
            AND ur.status = 'active'
            AND ur.deleted_at IS NULL
        """
            )
        )
        users_with_granular = result.scalar()

        # Total de permissões
        result = await db.execute(
            text("SELECT COUNT(*) FROM master.permissions WHERE is_active = true")
        )
        total_permissions = result.scalar()

        # Total de roles
        result = await db.execute(
            text("SELECT COUNT(*) FROM master.roles WHERE is_active = true")
        )
        total_roles = result.scalar()

        # Permissões mais usadas
        result = await db.execute(
            text(
                """
            SELECT
                p.name,
                p.display_name,
                COUNT(DISTINCT ur.user_id) as user_count
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            JOIN master.role_permissions rp ON r.id = rp.role_id
            JOIN master.permissions p ON rp.permission_id = p.id
            WHERE ur.status = 'active'
            AND ur.deleted_at IS NULL
            AND p.is_active = true
            GROUP BY p.name, p.display_name
            ORDER BY user_count DESC
            LIMIT 10
        """
            )
        )

        most_used_permissions = []
        for row in result.fetchall():
            most_used_permissions.append(
                {
                    "permission": row.name,
                    "display_name": row.display_name,
                    "user_count": row.user_count,
                }
            )

        # Distribuição por contexto
        result = await db.execute(
            text(
                """
            SELECT
                p.context_level,
                COUNT(DISTINCT ur.user_id) as user_count
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            JOIN master.role_permissions rp ON r.id = rp.role_id
            JOIN master.permissions p ON rp.permission_id = p.id
            WHERE ur.status = 'active'
            AND ur.deleted_at IS NULL
            AND p.is_active = true
            GROUP BY p.context_level
        """
            )
        )

        permission_distribution = {}
        for row in result.fetchall():
            permission_distribution[row.context_level] = row.user_count

        migration_coverage = (
            (users_with_granular / total_users * 100) if total_users > 0 else 0
        )

        return SystemPermissionStats(
            total_users=total_users,
            users_with_granular_permissions=users_with_granular,
            total_permissions=total_permissions,
            total_roles=total_roles,
            migration_coverage_percent=migration_coverage,
            most_used_permissions=most_used_permissions,
            permission_distribution=permission_distribution,
        )

    except Exception as e:
        logger.error("Error getting system stats", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post(
    "/migrate-user",
    summary="Migrar usuário individual",
    description="Migrar um usuário específico para o sistema granular",
    tags=["Permissions Admin"],
)
@require_permission(permission="system.admin", context_type="system")
async def migrate_single_user(
    user_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Migrar usuário individual para sistema granular:

    - **user_id**: ID do usuário
    - **force**: Forçar migração mesmo se já migrado
    """
    try:
        from sqlalchemy import text

        # Verificar se usuário existe
        user_check = await db.execute(
            text(
                """
            SELECT id, email_address FROM master.users WHERE id = :user_id AND deleted_at IS NULL
        """
            ),
            {"user_id": user_id},
        )

        user = user_check.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se já foi migrado
        if not force:
            migrated_check = await db.execute(
                text(
                    """
                SELECT ur.id FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id
                AND r.name LIKE 'granular_%'
                AND ur.status = 'active'
                AND ur.deleted_at IS NULL
            """
                ),
                {"user_id": user_id},
            )

            if migrated_check.fetchone():
                return {
                    "message": "Usuário já foi migrado",
                    "user_email": user.email_address,
                }

        # Buscar role atual do usuário para determinar template
        role_check = await db.execute(
            text(
                """
            SELECT r.level, r.name
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
            AND ur.status = 'active'
            AND ur.deleted_at IS NULL
            ORDER BY r.level DESC
            LIMIT 1
        """
            ),
            {"user_id": user_id},
        )

        user_role = role_check.fetchone()
        if not user_role:
            raise HTTPException(
                status_code=400, detail="Usuário não possui roles para migrar"
            )

        # Determinar template baseado no nível
        level = user_role.level
        if level >= 90:
            template_key = "super_admin"
        elif level >= 80:
            template_key = "admin_empresa"
        elif level >= 60:
            template_key = "admin_estabelecimento"
        elif level >= 50:
            template_key = "gerente_operacional"
        else:
            template_key = "operador"

        # Buscar role granular correspondente
        granular_role_check = await db.execute(
            text(
                """
            SELECT id FROM master.roles WHERE name = :role_name AND is_active = true
        """
            ),
            {"role_name": f"granular_{template_key}"},
        )

        granular_role = granular_role_check.fetchone()
        if not granular_role:
            raise HTTPException(
                status_code=500,
                detail=f"Role granular não encontrado: granular_{template_key}",
            )

        # Criar user_role granular
        await db.execute(
            text(
                """
            INSERT INTO master.user_roles (
                user_id, role_id, context_type, context_id,
                status, assigned_by_user_id, assigned_at,
                created_at, updated_at
            ) VALUES (
                :user_id, :role_id, 'establishment', NULL,
                'active', :assigned_by, NOW(),
                NOW(), NOW()
            )
        """
            ),
            {
                "user_id": user_id,
                "role_id": granular_role.id,
                "assigned_by": current_user.id,
            },
        )

        await db.commit()

        logger.info(
            "User migrated to granular permissions",
            user_id=user_id,
            user_email=user.email_address,
            template=template_key,
            original_level=level,
            migrated_by=current_user.id,
        )

        return {
            "message": "Usuário migrado com sucesso",
            "user_email": user.email_address,
            "template": template_key,
            "original_level": level,
        }

    except Exception as e:
        await db.rollback()
        logger.error(
            "Error migrating user", error=str(e), user_id=user_id, exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post(
    "/invalidate-cache",
    summary="Invalidar cache de permissões",
    description="Limpar cache de permissões para forçar recarregamento",
    tags=["Permissions Admin"],
)
@require_permission(permission="system.admin", context_type="system")
async def invalidate_permissions_cache(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Invalidar cache de permissões:

    - **user_id**: ID do usuário específico (opcional, se não fornecido limpa todo cache)
    """
    try:
        from app.infrastructure.cache.permission_cache import permission_cache

        if user_id:
            await permission_cache.invalidate_user_cache(user_id)
            message = f"Cache do usuário {user_id} invalidado"
        else:
            await permission_cache.clear_all_permission_cache()
            message = "Todo cache de permissões invalidado"

        logger.info(
            "Permission cache invalidated", user_id=user_id, cleared_by=current_user.id
        )

        return {"message": message}

    except Exception as e:
        logger.error("Error invalidating cache", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
