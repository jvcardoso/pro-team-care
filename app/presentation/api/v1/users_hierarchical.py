"""
API Endpoints para Gerenciamento Hierárquico de Usuários
Implementa controle de acesso baseado em hierarquia de permissões
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.hierarchical_user_repository import (
    HierarchicalUserRepository,
)
from app.infrastructure.repositories.user_repository_enhanced import (
    EnhancedUserRepository,
)

router = APIRouter(prefix="/hierarchical-users", tags=["Hierarchical Users"])


@router.get(
    "/hierarchical",
    summary="Listar usuários com controle hierárquico",
    description="""
    Lista usuários baseado no nível hierárquico do usuário solicitante:

    **Níveis de Acesso:**
    - 🔴 **ROOT**: Todos os usuários (dados mascarados)
    - 🔵 **Admin Empresa**: Usuários das empresas administradas
    - 🟢 **Admin Estabelecimento**: Usuários dos estabelecimentos
    - 🟡 **Usuário Comum**: Próprios dados + colegas

    **Filtros Disponíveis:**
    - `search`: Busca por nome ou email
    - `role_filter`: Filtrar por role específico
    - `company_filter`: Filtrar por empresa (apenas admins)
    - `establishment_filter`: Filtrar por estabelecimento
    - `hierarchy_filter`: Filtrar por nível hierárquico

    **Segurança:**
    - Controle automático de acesso baseado em hierarquia
    - Mascaramento de dados sensíveis por nível
    - Log de auditoria automático
    """,
    responses={
        200: {
            "description": "Lista de usuários acessíveis",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {
                                "user_id": 1,
                                "user_email": "admin@example.com",
                                "person_name": "Administrador",
                                "hierarchy_level": "ROOT",
                                "company_id": 1,
                                "establishment_code": "MATRIZ001",
                                "access_reason": "System Administrator - Full Access",
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "per_page": 50,
                        "requesting_user_hierarchy": "ROOT",
                    }
                }
            },
        },
        403: {"description": "Acesso negado - usuário sem permissões suficientes"},
        404: {"description": "Usuário solicitante não encontrado"},
    },
)
async def list_users_hierarchical(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(50, ge=1, le=100, description="Limite de registros por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    role_filter: Optional[str] = Query(None, description="Filtrar por role específico"),
    company_filter: Optional[int] = Query(
        None, description="Filtrar por ID da empresa"
    ),
    establishment_filter: Optional[int] = Query(
        None, description="Filtrar por ID do estabelecimento"
    ),
    hierarchy_filter: Optional[str] = Query(
        None, description="Filtrar por nível hierárquico"
    ),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Lista usuários com controle hierárquico completo"""

    # Inicializar repository hierárquico
    hierarchical_repo = HierarchicalUserRepository(db)

    try:
        # Obter usuários acessíveis
        users, total = await hierarchical_repo.list_accessible_users(
            requesting_user_id=current_user.id,
            skip=skip,
            limit=limit,
            search=search,
            role_filter=role_filter,
            company_filter=company_filter,
            establishment_filter=establishment_filter,
            hierarchy_filter=hierarchy_filter,
        )

        # Obter informações hierárquicas do usuário solicitante
        requester_hierarchy = await hierarchical_repo.get_user_hierarchy_info(
            current_user.id
        )

        return {
            "users": users,
            "total": total,
            "page": (skip // limit) + 1,
            "per_page": limit,
            "requesting_user_hierarchy": (
                requester_hierarchy.get("hierarchy_level")
                if requester_hierarchy
                else "UNKNOWN"
            ),
            "requesting_user_contexts": {
                "companies": (
                    requester_hierarchy.get("accessible_companies", [])
                    if requester_hierarchy
                    else []
                ),
                "establishments": (
                    requester_hierarchy.get("accessible_establishments", [])
                    if requester_hierarchy
                    else []
                ),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}",
        )


@router.get(
    "/{user_id}/hierarchical",
    summary="Obter usuário específico com controle hierárquico",
    description="""
    Busca dados detalhados de um usuário específico baseado na hierarquia:

    **Níveis de Retorno:**
    - 🔴 **ROOT**: Dados completos com mascaramento de segurança
    - 🔵 **Admin Empresa**: Dados empresariais (se usuário da mesma empresa)
    - 🟢 **Admin Estabelecimento**: Dados básicos (se usuário do mesmo estabelecimento)
    - 🟡 **Usuário Comum**: Próprios dados completos ou dados básicos de colegas

    **Campos Retornados por Nível:**
    - ROOT: Todos + status 2FA + dados LGPD
    - Admin Empresa: Dados empresariais + histórico
    - Admin Estabelecimento: Dados básicos + role
    - Usuário: Dados pessoais ou básicos de colegas
    """,
    responses={
        200: {"description": "Dados do usuário (conforme nível de acesso)"},
        403: {"description": "Acesso negado ao usuário solicitado"},
        404: {"description": "Usuário não encontrado ou sem acesso"},
    },
)
async def get_user_hierarchical(
    user_id: int = Path(..., description="ID do usuário a ser consultado"),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """Busca usuário específico com controle hierárquico"""

    # Inicializar repository hierárquico
    hierarchical_repo = HierarchicalUserRepository(db)

    try:
        # Buscar usuário com controle hierárquico
        user_data = await hierarchical_repo.get_user_with_hierarchical_control(
            requesting_user_id=current_user.id, target_user_id=user_id
        )

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado ou acesso negado",
            )

        # Obter informações de contexto
        requester_hierarchy = await hierarchical_repo.get_user_hierarchy_info(
            current_user.id
        )

        # Adicionar metadados de controle
        user_data["_access_metadata"] = {
            "requesting_user_id": current_user.id,
            "requesting_user_hierarchy": (
                requester_hierarchy.get("hierarchy_level")
                if requester_hierarchy
                else "UNKNOWN"
            ),
            "accessed_at": user_data.get("accessed_at"),
            "access_reason": user_data.get("access_reason", "Direct access"),
        }

        return user_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}",
        )


@router.get(
    "/hierarchy-info",
    summary="Informações da hierarquia do usuário atual",
    description="""
    Retorna informações detalhadas sobre o nível hierárquico e contextos
    de acesso do usuário autenticado.

    **Informações Retornadas:**
    - Nível hierárquico (ROOT, ADMIN_EMPRESA, ADMIN_ESTABELECIMENTO, USUARIO_COMUM)
    - Lista de empresas acessíveis
    - Lista de estabelecimentos acessíveis
    - Roles e permissões ativas
    - Estatísticas de usuários acessíveis
    """,
    responses={
        200: {
            "description": "Informações hierárquicas do usuário",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": 5,
                        "user_email": "admin@proteamcare.com",
                        "person_name": "Administrador",
                        "hierarchy_level": "ROOT",
                        "accessible_companies": [],
                        "accessible_establishments": [],
                        "accessible_users_count": 9,
                        "roles_and_permissions": {
                            "roles": [],
                            "permissions": {},
                            "establishments": [],
                        },
                    }
                }
            },
        }
    },
)
async def get_current_user_hierarchy_info(
    current_user=Depends(get_current_user), db=Depends(get_db)
) -> Dict[str, Any]:
    """Obtém informações hierárquicas do usuário atual"""

    # Inicializar repository hierárquico
    hierarchical_repo = HierarchicalUserRepository(db)

    try:
        # Obter informações hierárquicas
        hierarchy_info = await hierarchical_repo.get_user_hierarchy_info(
            current_user.id
        )

        if not hierarchy_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Informações hierárquicas não encontradas para o usuário",
            )

        # Obter roles e permissões
        enhanced_repo = EnhancedUserRepository(db)
        roles_permissions = await enhanced_repo.get_user_roles_and_permissions(
            current_user.id
        )

        # Contar usuários acessíveis
        accessible_users = await hierarchical_repo._get_accessible_user_ids(
            current_user.id
        )

        # Compilar resposta completa
        response = {
            **hierarchy_info,
            "accessible_users_count": len(accessible_users),
            "roles_and_permissions": roles_permissions,
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}",
        )


@router.get(
    "/accessible-users-summary",
    summary="Resumo de usuários acessíveis",
    description="""
    Retorna um resumo estatístico dos usuários acessíveis pelo usuário atual,
    agrupados por nível hierárquico e contexto.

    **Métricas Incluídas:**
    - Total de usuários acessíveis
    - Distribuição por nível hierárquico
    - Distribuição por empresa/estabelecimento
    - Estatísticas de atividade (últimos logins)
    """,
    responses={
        200: {
            "description": "Resumo estatístico dos usuários acessíveis",
            "content": {
                "application/json": {
                    "example": {
                        "total_accessible_users": 9,
                        "by_hierarchy": {
                            "ROOT": 4,
                            "ADMIN_EMPRESA": 0,
                            "ADMIN_ESTABELECIMENTO": 0,
                            "USUARIO_COMUM": 5,
                        },
                        "by_access_level": {
                            "full": 9,
                            "company": 0,
                            "establishment": 0,
                            "self": 1,
                        },
                        "activity_summary": {
                            "active_last_30_days": 2,
                            "never_logged_in": 7,
                        },
                    }
                }
            },
        }
    },
)
async def get_accessible_users_summary(
    current_user=Depends(get_current_user), db=Depends(get_db)
) -> Dict[str, Any]:
    """Resumo estatístico dos usuários acessíveis"""

    # Inicializar repository hierárquico
    hierarchical_repo = HierarchicalUserRepository(db)

    try:
        # Obter todos os usuários acessíveis (sem paginação)
        users, total = await hierarchical_repo.list_accessible_users(
            requesting_user_id=current_user.id,
            skip=0,
            limit=1000,  # Limite alto para pegar todos
        )

        # Compilar estatísticas
        stats = {
            "total_accessible_users": total,
            "by_hierarchy": {},
            "by_access_level": {},
            "activity_summary": {"active_last_30_days": 0, "never_logged_in": 0},
        }

        # Analisar usuários
        for user in users:
            # Por hierarquia
            hierarchy = user.get("hierarchy_level", "UNKNOWN")
            stats["by_hierarchy"][hierarchy] = (
                stats["by_hierarchy"].get(hierarchy, 0) + 1
            )

            # Por nível de acesso
            access_reason = user.get("access_reason", "")
            if "Full Access" in access_reason:
                access_level = "full"
            elif "Company" in access_reason:
                access_level = "company"
            elif "Establishment" in access_reason:
                access_level = "establishment"
            else:
                access_level = "self"

            stats["by_access_level"][access_level] = (
                stats["by_access_level"].get(access_level, 0) + 1
            )

            # Atividade
            last_login = user.get("user_last_login_at")
            if last_login is None:
                stats["activity_summary"]["never_logged_in"] += 1
            else:
                # Simplificado - assumir que teve login recente se tem data
                stats["activity_summary"]["active_last_30_days"] += 1

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}",
        )
