from typing import Dict, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.role_repository import (
    PermissionRepository,
    RoleRepository,
)
from app.presentation.decorators.simple_permissions import (
    require_permission,
    require_system_admin,
)
from app.presentation.schemas.role import (
    PermissionListParams,
    PermissionListResponse,
    PermissionResponse,
    RoleCreate,
    RoleDetailed,
    RoleListParams,
    RoleListResponse,
    RoleResponse,
    RoleUpdate,
)

logger = structlog.get_logger()

router = APIRouter()


# ==========================================
# ROLES ENDPOINTS
# ==========================================


@router.post(
    "/",
    response_model=RoleDetailed,
    status_code=status.HTTP_201_CREATED,
    summary="Criar perfil",
    description="Criar novo perfil com permissões",
    tags=["Roles"],
)
@require_permission(permission="roles.create", context_type="establishment")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Criar novo perfil:

    - **name**: Nome técnico único do perfil
    - **display_name**: Nome de exibição do perfil
    - **description**: Descrição detalhada (opcional)
    - **level**: Nível hierárquico (10-100)
    - **context_type**: Contexto (system, company, establishment)
    - **is_active**: Status ativo (padrão: true)
    - **permission_ids**: Lista de IDs das permissões (opcional)
    - **settings**: Configurações específicas (opcional)
    """
    try:
        logger.info("=== INÍCIO CRIAÇÃO ROLE ===")
        logger.info("Dados recebidos", role_data=role_data.model_dump())

        repository = RoleRepository(db)

        # Check if name already exists
        existing_role = await repository.get_by_name(role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=400, detail=f"Perfil com nome '{role_data.name}' já existe"
            )

        role = await repository.create(role_data)
        logger.info(
            "Role created",
            role_id=role.id,
            name=role.name,
            display_name=role.display_name,
        )

        return role

    except ValueError as e:
        logger.error("ValueError em create_role", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating role", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get(
    "/",
    response_model=RoleListResponse,
    summary="Listar perfis",
    description="Listar perfis com filtros e paginação",
    tags=["Roles"],
)
@require_permission(permission="users_manage_roles", context_type="system")
async def list_roles(
    skip: int = Query(
        0, ge=0, description="Número de registros para pular (paginação)"
    ),
    limit: int = Query(
        10, ge=1, le=100, description="Máximo de registros para retornar (1-100)"
    ),
    context_type: str = Query(None, description="Filtrar por contexto"),
    is_active: bool = Query(None, description="Filtrar por status ativo"),
    is_system_role: bool = Query(None, description="Filtrar perfis do sistema"),
    level_min: int = Query(None, ge=10, le=100, description="Nível mínimo"),
    level_max: int = Query(None, ge=10, le=100, description="Nível máximo"),
    search: str = Query(
        None, min_length=1, max_length=100, description="Buscar por nome ou descrição"
    ),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Listar perfis com filtros opcionais:

    - **skip**: Número de registros para pular (paginação)
    - **limit**: Máximo de registros para retornar (1-100)
    - **context_type**: system, company ou establishment
    - **is_active**: true para ativos, false para inativos
    - **is_system_role**: true para perfis do sistema
    - **level_min/level_max**: Filtro por faixa de nível
    - **search**: Busca por nome, nome de exibição ou descrição
    """
    try:
        # Convert skip/limit to page/size for internal use
        page = (skip // limit) + 1 if limit > 0 else 1
        size = limit

        params = RoleListParams(
            context_type=context_type,
            is_active=is_active,
            is_system_role=is_system_role,
            level_min=level_min,
            level_max=level_max,
            search=search,
            page=page,
            size=size,
        )

        repository = RoleRepository(db)
        roles, total = await repository.list_roles(params)

        total_pages = (total + size - 1) // size

        return RoleListResponse(
            roles=roles,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error("Error listing roles", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get(
    "/count",
    summary="Contar perfis",
    description="Retorna o total de perfis que atendem aos critérios de filtro",
    tags=["Roles"],
)
async def count_roles(
    context_type: str = Query(None, description="Filtrar por contexto"),
    is_active: bool = Query(None, description="Filtrar por status ativo"),
    is_system_role: bool = Query(None, description="Filtrar perfis do sistema"),
    level_min: int = Query(None, ge=10, le=100, description="Nível mínimo"),
    level_max: int = Query(None, ge=10, le=100, description="Nível máximo"),
    search: str = Query(
        None, min_length=1, max_length=100, description="Buscar por nome ou descrição"
    ),
    db=Depends(get_db),
):
    """
    Contar perfis com filtros:

    - **Útil para**: Implementar paginação no frontend, estatísticas
    - Aplica os mesmos filtros do endpoint de listagem
    - Retorna apenas o número total
    """
    try:
        params = RoleListParams(
            context_type=context_type,
            is_active=is_active,
            is_system_role=is_system_role,
            level_min=level_min,
            level_max=level_max,
            search=search,
            page=1,
            size=1,  # We only need the count
        )

        repository = RoleRepository(db)
        _, total = await repository.list_roles(params)

        return {"total": total}

    except Exception as e:
        logger.error("Error counting roles", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


# ==========================================
# UTILITY ENDPOINTS (before parameterized routes)
# ==========================================


@router.get(
    "/context-types",
    response_model=List[str],
    summary="Listar tipos de contexto",
    description="Listar tipos de contexto disponíveis",
    tags=["Roles"],
)
async def get_context_types():
    """
    Listar tipos de contexto disponíveis:

    - system: Contexto global do sistema
    - company: Contexto de empresa
    - establishment: Contexto de estabelecimento
    """
    return ["system", "company", "establishment"]


@router.get(
    "/levels",
    response_model=Dict[int, str],
    summary="Listar níveis hierárquicos",
    description="Listar níveis hierárquicos e suas descrições",
    tags=["Roles"],
)
async def get_role_levels():
    """
    Listar níveis hierárquicos:

    - 10-30: Níveis básicos (Visualizador, Operador)
    - 40-60: Níveis intermediários (Profissional, Gerente)
    - 70-80: Níveis administrativos (Admin Estabelecimento/Empresa)
    - 90-100: Níveis do sistema (Super Admin)
    """
    return {
        10: "Básico - Visualizador",
        20: "Básico - Consultor",
        30: "Básico - Operador",
        40: "Intermediário - Profissional",
        50: "Intermediário - Auditor",
        60: "Intermediário - Gerente",
        70: "Administrativo - Admin Estabelecimento",
        80: "Administrativo - Admin Empresa",
        90: "Sistema - Admin Sistema",
        100: "Sistema - Super Admin",
    }


@router.get(
    "/{role_id}",
    response_model=RoleDetailed,
    summary="Buscar perfil",
    description="Buscar perfil por ID com permissões",
    tags=["Roles"],
)
async def get_role(role_id: int, db=Depends(get_db)):
    """
    Buscar perfil específico por ID:

    - Retorna dados completos do perfil
    - Inclui lista de permissões associadas
    - Inclui metadados de criação/atualização
    """
    try:
        repository = RoleRepository(db)
        role = await repository.get_by_id(role_id)

        if not role:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        return role

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting role", error=str(e), role_id=role_id, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.put(
    "/{role_id}",
    response_model=RoleDetailed,
    summary="Atualizar perfil",
    description="Atualizar perfil existente",
    tags=["Roles"],
)
async def update_role(role_id: int, role_data: RoleUpdate, db=Depends(get_db)):
    """
    Atualizar perfil existente:

    - Todos os campos são opcionais
    - Perfis do sistema não podem ser editados
    - Nome deve ser único se alterado
    - Permissões podem ser atualizadas via permission_ids
    """
    try:
        repository = RoleRepository(db)

        # Check if name conflict (if name is being changed)
        if role_data.name:
            existing_role = await repository.get_by_name(role_data.name)
            if existing_role and existing_role.id != role_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Perfil com nome '{role_data.name}' já existe",
                )

        role = await repository.update(role_id, role_data)

        if not role:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        logger.info(
            "Role updated",
            role_id=role_id,
            name=role.name,
            changes=role_data.model_dump(exclude_unset=True),
        )

        return role

    except ValueError as e:
        logger.error("ValueError em update_role", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating role", error=str(e), role_id=role_id, exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir perfil",
    description="Excluir perfil (soft delete se em uso)",
    tags=["Roles"],
)
async def delete_role(role_id: int, db=Depends(get_db)):
    """
    Excluir perfil:

    - Perfis do sistema não podem ser excluídos
    - Se o perfil estiver em uso, será desativado (soft delete)
    - Se não estiver em uso, será removido permanentemente
    - Remove todas as permissões associadas
    """
    try:
        repository = RoleRepository(db)
        success = await repository.delete(role_id)

        if not success:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        logger.info("Role deleted", role_id=role_id)

        # No return for 204 status code

    except ValueError as e:
        logger.error("ValueError em delete_role", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting role", error=str(e), role_id=role_id, exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


# ==========================================
# PERMISSIONS ENDPOINTS
# ==========================================


@router.get(
    "/permissions/",
    response_model=PermissionListResponse,
    summary="Listar permissões",
    description="Listar permissões disponíveis",
    tags=["Permissions"],
)
async def list_permissions(
    module: str = Query(None, description="Filtrar por módulo"),
    action: str = Query(None, description="Filtrar por ação"),
    resource: str = Query(None, description="Filtrar por recurso"),
    context_level: str = Query(None, description="Filtrar por contexto"),
    is_active: bool = Query(None, description="Filtrar por status ativo"),
    search: str = Query(
        None, min_length=1, max_length=100, description="Buscar por nome ou descrição"
    ),
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(50, ge=1, le=200, description="Itens por página"),
    db=Depends(get_db),
):
    """
    Listar permissões disponíveis:

    - **module**: admin, clinical, etc.
    - **action**: view, create, edit, delete
    - **resource**: users, companies, establishments
    - **context_level**: system, company, establishment
    - **is_active**: true para ativas
    - **search**: Busca por nome ou descrição
    """
    try:
        params = PermissionListParams(
            module=module,
            action=action,
            resource=resource,
            context_level=context_level,
            is_active=is_active,
            search=search,
            page=page,
            size=size,
        )

        repository = PermissionRepository(db)
        permissions, total = await repository.list_permissions(params)

        total_pages = (total + size - 1) // size

        return PermissionListResponse(
            permissions=permissions,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error("Error listing permissions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get(
    "/permissions/grouped",
    response_model=Dict[str, List[PermissionResponse]],
    summary="Listar permissões agrupadas",
    description="Listar permissões agrupadas por módulo",
    tags=["Permissions"],
)
async def list_permissions_grouped(db=Depends(get_db)):
    """
    Listar permissões agrupadas por módulo:

    - Retorna dicionário com módulos como chaves
    - Cada módulo contém lista de permissões
    - Útil para construir interfaces de seleção
    - Apenas permissões ativas são retornadas
    """
    try:
        repository = PermissionRepository(db)
        grouped_permissions = await repository.get_permissions_grouped_by_module()

        return grouped_permissions

    except Exception as e:
        logger.error("Error listing grouped permissions", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get(
    "/{role_id}/permissions",
    response_model=List[PermissionResponse],
    summary="Buscar permissões do perfil",
    description="Buscar permissões associadas a um perfil",
    tags=["Roles"],
)
async def get_role_permissions(role_id: int, db=Depends(get_db)):
    """
    Buscar permissões de um perfil específico:

    - Retorna lista de permissões ativas do perfil
    - Ordenado por módulo e ação
    - Inclui detalhes completos de cada permissão
    """
    try:
        repository = RoleRepository(db)

        # Verify role exists
        role = await repository.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        permissions = await repository.get_role_permissions(role_id)
        return permissions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting role permissions",
            error=str(e),
            role_id=role_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )
