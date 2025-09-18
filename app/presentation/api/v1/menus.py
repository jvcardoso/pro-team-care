"""
Menus API - Sistema de Menus Dinâmicos
Endpoints para buscar menus baseado em permissões e contexto do usuário
"""

import os
from typing import Any, Dict, List, Optional, Union

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.domain.repositories.menu_repository import MenuRepository
from app.infrastructure.auth import get_current_user_skip_options
from app.infrastructure.database import get_db
from app.infrastructure.services.tenant_context_service import get_tenant_context

logger = structlog.get_logger()
router = APIRouter(tags=["menus"])


# Pydantic models para documentação OpenAPI
class MenuItem(BaseModel):
    """Modelo de um item de menu"""

    id: int = Field(..., description="ID único do menu")
    parent_id: Optional[int] = Field(None, description="ID do menu pai")
    name: str = Field(..., description="Nome do menu")
    slug: str = Field(..., description="Slug único do menu")
    url: Optional[str] = Field(None, description="URL do menu")
    route_name: Optional[str] = Field(None, description="Nome da rota")
    route_params: Optional[str] = Field(None, description="Parâmetros da rota")
    icon: Optional[str] = Field(None, description="Ícone do menu")
    level: int = Field(..., description="Nível na hierarquia")
    sort_order: int = Field(..., description="Ordem de classificação")
    badge_text: Optional[str] = Field(None, description="Texto do badge")
    badge_color: Optional[str] = Field(None, description="Cor do badge")
    full_path_name: str = Field(..., description="Caminho completo do menu")
    id_path: Union[str, List[int]] = Field(
        ..., description="Caminho de IDs (string ou lista)"
    )
    type: str = Field(..., description="Tipo do menu")
    permission_name: Optional[str] = Field(None, description="Nome da permissão")
    children: List[Dict[str, Any]] = Field(
        default_factory=list, description="Menus filhos"
    )

    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    """Informações do usuário"""

    email: str = Field(..., description="Email do usuário")
    name: str = Field(..., description="Nome do usuário")
    person_type: str = Field(..., description="Tipo de pessoa")
    is_root: bool = Field(..., description="Se é usuário ROOT")


class ContextInfo(BaseModel):
    """Informações do contexto"""

    type: str = Field(..., description="Tipo do contexto")
    id: Optional[int] = Field(None, description="ID do contexto")
    name: str = Field(..., description="Nome do contexto")
    description: str = Field(..., description="Descrição do contexto")


class MenuResponse(BaseModel):
    """Resposta da API de menus"""

    user_id: int = Field(..., description="ID do usuário")
    user_info: UserInfo = Field(..., description="Informações do usuário")
    context: ContextInfo = Field(..., description="Informações do contexto")
    total_menus: int = Field(..., description="Total de menus retornados")
    include_dev_menus: bool = Field(
        ..., description="Se incluiu menus de desenvolvimento"
    )
    menus: List[MenuItem] = Field(..., description="Lista hierárquica de menus")
    success: Optional[bool] = Field(None, description="Indicador de sucesso")
    message: Optional[str] = Field(None, description="Mensagem opcional")


class HealthResponse(BaseModel):
    """Resposta do health check"""

    service: str = Field(..., description="Nome do serviço")
    status: str = Field(..., description="Status do serviço")
    version: str = Field(..., description="Versão do serviço")
    endpoints: List[str] = Field(..., description="Endpoints disponíveis")
    environment: str = Field(..., description="Ambiente de execução")


@router.get("/user/{user_id}")
async def get_user_dynamic_menus(
    user_id: int,
    request: Request,
    context_type: str = Query(
        "establishment", description="Tipo de contexto (system/company/establishment)"
    ),
    context_id: Optional[int] = Query(None, description="ID do contexto específico"),
    include_dev_menus: Optional[bool] = Query(
        None, description="Incluir menus de desenvolvimento (apenas ROOT)"
    ),
    current_user=Depends(get_current_user_skip_options),
    db=Depends(get_db),
) -> Dict[str, Any]:
    """
    Retorna menus dinâmicos permitidos para o usuário no contexto atual.

    **Funcionalidades:**
    - Filtra menus baseado nas permissões do usuário
    - Respeita contexto multi-tenant (system/company/establishment)
    - Tratamento especial para usuários ROOT
    - Auditoria de acesso para administradores
    - Fallback seguro em caso de erro

    **Parâmetros:**
    - `user_id`: ID do usuário alvo
    - `context_type`: Tipo de contexto (system/company/establishment)
    - `context_id`: ID do contexto específico
    - `include_dev_menus`: Incluir menus de desenvolvimento (só ROOT)

    **Segurança:**
    - Usuários só podem ver próprios menus
    - ROOT pode ver menus de qualquer usuário (com auditoria)
    - Validação dupla de permissões
    """
    # Removido o exemplo JSON da docstring para usar response_model

    # Handle OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {
            "success": True,
            "menus": [],
            "user_info": {},
            "context": {},
            "total_menus": 0,
            "message": "OPTIONS request",
        }

    # current_user pode ser None para requests OPTIONS
    if current_user is None:
        return {
            "success": False,
            "menus": [],
            "user_info": {},
            "context": {},
            "total_menus": 0,
            "message": "Authentication required",
        }

    # Capturar IP para auditoria
    client_ip = request.client.host if request.client else None

    logger.info(
        "Solicitação de menus dinâmicos",
        user_id=user_id,
        context_type=context_type,
        context_id=context_id,
        requested_by=current_user.id,
        client_ip=client_ip,
    )

    # 🔒 VALIDAÇÃO CRÍTICA: Quem pode ver menus de quem?
    if current_user.id != user_id:
        # Verificar se current_user pode ver menus de outro usuário
        if not current_user.is_system_admin:
            logger.warning(
                "Acesso negado: usuário tentou ver menus de outro",
                requesting_user=current_user.id,
                target_user=user_id,
                client_ip=client_ip,
            )

            raise HTTPException(
                status_code=403,
                detail="Acesso negado: apenas administradores do sistema podem visualizar menus de outros usuários",
            )

        # ROOT vendo menus de outro usuário - LOG de auditoria
        logger.warning(
            "ROOT acessando menus de outro usuário",
            root_user=current_user.id,
            root_email=getattr(current_user, "email_address", "unknown"),
            target_user=user_id,
            context_type=context_type,
            client_ip=client_ip,
        )

    try:
        # Set tenant context for RLS
        tenant_service = get_tenant_context()
        await tenant_service.set_database_context(db, current_user.company_id)

        menu_repo = MenuRepository(db)

        # Buscar informações do usuário alvo
        target_user_info = await menu_repo.get_user_info(user_id)

        if not target_user_info:
            raise HTTPException(
                status_code=404, detail=f"Usuário {user_id} não encontrado"
            )

        if not target_user_info.get("is_active", False):
            raise HTTPException(
                status_code=403, detail=f"Usuário {user_id} está inativo"
            )

        # Determinar se deve incluir menus de desenvolvimento
        # ROOT pode solicitar explicitamente, ou auto em development
        if include_dev_menus is None:
            environment = os.getenv("ENVIRONMENT", "production")
            include_dev_menus = target_user_info.get("is_system_admin", False) and (
                context_type == "system" or environment == "development"
            )

        # Garantir que include_dev_menus seja bool
        include_dev_menus = bool(include_dev_menus)

        # Usuário não-ROOT nunca pode ver dev menus, mesmo se solicitado
        if not target_user_info.get("is_system_admin", False):
            include_dev_menus = False

        # Buscar menus do usuário
        flat_menus = await menu_repo.get_user_menus(
            user_id=user_id,
            context_type=context_type,
            context_id=context_id,
            include_dev_menus=include_dev_menus or False,
        )

        # Converter para árvore hierárquica
        menu_tree = await menu_repo.get_menu_tree(flat_menus)

        # Buscar informações do contexto
        context_info = await menu_repo.get_context_info(context_type, context_id)

        # Log de auditoria para ROOT
        if target_user_info.get("is_system_admin", False):
            await menu_repo.log_menu_access(
                user_id=user_id,
                context_type=context_type,
                context_id=context_id,
                total_menus=len(flat_menus),
                is_root=True,
                ip_address=client_ip,
            )

        # Resultado final
        result = {
            "user_id": user_id,
            "user_info": {
                "email": target_user_info.get("email"),
                "name": target_user_info.get("name"),
                "person_type": target_user_info.get("person_type"),
                "is_root": target_user_info.get("is_system_admin", False),
            },
            "context": context_info,
            "total_menus": len(flat_menus),
            "include_dev_menus": include_dev_menus,
            "menus": menu_tree,
            "success": True,
            "message": None,
        }

        logger.info(
            "Menus dinâmicos retornados com sucesso",
            user_id=user_id,
            total_menus=len(flat_menus),
            is_root=target_user_info.get("is_system_admin", False),
            context_type=context_type,
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (já formatadas)
        raise

    except Exception as e:
        logger.error(
            "Erro interno ao buscar menus dinâmicos",
            user_id=user_id,
            context_type=context_type,
            error=str(e),
            requesting_user=current_user.id,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor ao buscar menus: {str(e)}",
        )


@router.get("/user/{user_id}/context/{context_type}")
async def get_user_menus_by_context(
    user_id: int,
    context_type: str,
    request: Request,
    context_id: Optional[int] = Query(None, description="ID do contexto específico"),
    current_user=Depends(get_current_user_skip_options),
    db=Depends(get_db),
):
    """
    Endpoint alternativo para buscar menus por contexto específico.
    Útil para mudanças de contexto dinâmicas no frontend.

    **Parâmetros:**
    - `user_id`: ID do usuário
    - `context_type`: Tipo obrigatório no path (system/company/establishment)
    - `context_id`: ID opcional do contexto

    **Validações:**
    - context_type deve ser válido (system/company/establishment)
    - Mesmas validações de segurança do endpoint principal
    """

    # Handle OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {
            "success": True,
            "menus": [],
            "user_info": {},
            "context": {},
            "total_menus": 0,
            "message": "OPTIONS request",
        }

    # current_user pode ser None para requests OPTIONS
    if current_user is None:
        return {
            "success": False,
            "menus": [],
            "user_info": {},
            "context": {},
            "total_menus": 0,
            "message": "Authentication required",
        }

    # Validar context_type
    valid_contexts = ["system", "company", "establishment"]
    if context_type not in valid_contexts:
        raise HTTPException(
            status_code=400,
            detail=f"Contexto '{context_type}' inválido. Use: {', '.join(valid_contexts)}",
        )

    # Redirecionar para endpoint principal com parâmetros corretos
    return await get_user_dynamic_menus(
        user_id=user_id,
        request=request,
        context_type=context_type,
        context_id=context_id,
        include_dev_menus=None,  # Auto-determine
        current_user=current_user,
        db=db,
    )


@router.get("/menus/health")
async def menu_service_health():
    """
    Health check para o serviço de menus.
    Útil para monitoramento e debugging.
    """

    return {
        "service": "menu_service",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": [
            "GET /menus/user/{user_id}",
            "GET /menus/user/{user_id}/context/{context_type}",
            "GET /menus/menus/health",
        ],
        "environment": os.getenv("ENVIRONMENT", "production"),
    }


@router.get("/debug/structure")
async def debug_menu_structure(
    current_user=Depends(get_current_user_skip_options), db=Depends(get_db)
):
    """
    Endpoint de debug para visualizar estrutura completa de menus.
    Apenas para ROOT e environment development.
    """

    # current_user pode ser None para requests OPTIONS
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Só ROOT em development
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=403, detail="Acesso negado: apenas administradores do sistema"
        )

    environment = os.getenv("ENVIRONMENT", "production")
    if environment != "development":
        raise HTTPException(
            status_code=403, detail="Endpoint disponível apenas em development"
        )

    try:
        # Buscar estrutura completa de menus
        query = text(
            """
            SELECT
                id, parent_id, name, slug, permission_name,
                level, sort_order, is_active,
                company_specific, establishment_specific
            FROM master.vw_menu_hierarchy
            ORDER BY level, sort_order, name
        """
        )

        result = await db.execute(query)
        menus = [dict(row._mapping) for row in result.fetchall()]

        # Estatísticas
        stats = {
            "total_menus": len(menus),
            "levels": len(set(menu["level"] for menu in menus)),
            "company_specific": len([m for m in menus if m.get("company_specific")]),
            "establishment_specific": len(
                [m for m in menus if m.get("establishment_specific")]
            ),
            "with_permissions": len([m for m in menus if m.get("permission_name")]),
        }

        return {
            "debug": True,
            "environment": environment,
            "stats": stats,
            "menus": menus,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar estrutura: {str(e)}"
        )
