"""
Menus CRUD API - Presentation Layer
Endpoints FastAPI completos para sistema de menus dinâmicos
"""

import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.cache.menu_cache_service import get_menu_cache_service, MenuCacheService
from app.infrastructure.repositories.menu_repository_optimized import MenuRepositoryOptimized
from app.application.use_cases.menu_use_cases import (
    CreateMenuUseCase, UpdateMenuUseCase, DeleteMenuUseCase, 
    GetMenuTreeUseCase, ReorderMenusUseCase, SearchMenusUseCase,
    GetMenuStatisticsUseCase, BulkUpdateMenusUseCase,
    MenuUseCaseException, MenuValidationException, MenuHierarchyException
)
from app.application.dto.menu_dto import (
    MenuCreateDTO, MenuUpdateDTO, MenuSearchRequestDTO, 
    ReorderRequestDTO, BulkUpdateRequestDTO
)
from app.presentation.schemas.menu import (
    MenuCreateSchema, MenuUpdateSchema, MenuDetailedSchema, MenuListSchema, 
    MenuTreeResponseSchema, ReorderRequestSchema, MenuSearchRequestSchema,
    MenuSearchResponse, MenuStatisticsSchema, BulkUpdateRequestSchema,
    MenuOperationResultSchema, MenuHealthSchema, MenuListResponse,
    MenuErrorResponse, MenuPathSchema
)
from app.infrastructure.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/menus/crud", tags=["Menus CRUD"])
logger = get_logger()


# Dependency injection
async def get_menu_repository(
    db: AsyncSession = Depends(get_db),
    cache_service: MenuCacheService = Depends(get_menu_cache_service)
) -> MenuRepositoryOptimized:
    """Dependency para obter repository de menus"""
    return MenuRepositoryOptimized(db, cache_service)


def handle_menu_exceptions(e: Exception, operation: str, **context):
    """Handler centralizado para exceções de menu"""
    logger.error(f"Erro em {operation}", error=str(e), **context)
    
    if isinstance(e, MenuValidationException):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    elif isinstance(e, MenuHierarchyException):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    elif isinstance(e, MenuUseCaseException):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post(
    "/",
    response_model=MenuDetailedSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Menu",
    description="""
    Cria um novo menu na hierarquia do sistema.
    
    **Funcionalidades:**
    - Validação automática de hierarquia (máximo 5 níveis)
    - Slug único por nível
    - Auto-ordenação (sort_order)
    - Invalidação automática de cache
    - Recálculo de caminhos hierárquicos
    
    **Validações:**
    - Nome e slug obrigatórios
    - Slug deve ser único no nível pai
    - Menu pai deve existir (se informado)
    - Permissão deve existir no sistema (se informada)
    - Máximo 5 níveis de profundidade
    
    **Performance:**
    - Cache automático do menu criado
    - Invalidação inteligente de caches relacionados
    """,
    responses={
        201: {
            "description": "Menu criado com sucesso",
            "model": MenuDetailedSchema
        },
        400: {
            "description": "Dados inválidos ou hierarquia inválida",
            "model": MenuErrorResponse
        },
        401: {"description": "Não autorizado"},
        409: {"description": "Slug já existe no nível"}
    }
)
async def create_menu(
    menu_data: MenuCreateSchema,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Criar novo menu com validações completas"""
    
    try:
        # Converter schema para DTO
        create_dto = MenuCreateDTO(
            parent_id=menu_data.parent_id,
            name=menu_data.name,
            slug=menu_data.slug,
            url=menu_data.url,
            route_name=menu_data.route_name,
            route_params=menu_data.route_params,
            icon=menu_data.icon,
            menu_type=menu_data.menu_type,
            permission_name=menu_data.permission_name,
            company_specific=menu_data.company_specific,
            establishment_specific=menu_data.establishment_specific,
            badge_text=menu_data.badge_text,
            badge_color=menu_data.badge_color,
            css_class=menu_data.css_class,
            description=menu_data.description,
            help_text=menu_data.help_text,
            keywords=menu_data.keywords,
            is_visible=menu_data.is_visible,
            visible_in_menu=menu_data.visible_in_menu
        )
        
        # Executar use case
        use_case = CreateMenuUseCase(repository)
        result = await use_case.execute(create_dto, current_user.id)
        
        logger.info("Menu criado via API", 
                   menu_id=result.id, 
                   name=result.name,
                   created_by=current_user.id)
        
        # Converter entity para schema de resposta
        return MenuDetailedSchema(
            id=result.id,
            parent_id=result.parent_id,
            name=result.name,
            slug=result.slug,
            url=result.url,
            route_name=result.route_name,
            route_params=result.route_params,
            level=result.level,
            sort_order=result.sort_order,
            menu_type=result.menu_type,
            status=result.status,
            is_visible=result.is_visible,
            visible_in_menu=result.visible_in_menu,
            permission_name=result.permission_name,
            company_specific=result.company_specific,
            establishment_specific=result.establishment_specific,
            icon=result.icon,
            badge_text=result.badge_text,
            badge_color=result.badge_color,
            css_class=result.css_class,
            description=result.description,
            help_text=result.help_text,
            keywords=result.keywords,
            full_path_name=result.full_path_name,
            id_path=result.id_path,
            has_children=result.has_children(),
            children_count=len(result.children),
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by
        )
        
    except (MenuValidationException, MenuHierarchyException, MenuUseCaseException) as e:
        handle_menu_exceptions(e, "create_menu", user_id=current_user.id)


@router.get(
    "/",
    response_model=MenuListResponse,
    summary="Listar Menus",
    description="""
    Lista menus com filtros e paginação otimizada.
    
    **Performance:**
    - Cache automático (TTL 10 minutos)
    - Índices otimizados no banco
    - Lazy loading de relacionamentos
    
    **Filtros:**
    - `parent_id`: Filtrar por menu pai (None = raiz)
    - `status`: Filtrar por status (active, inactive, draft)
    - `search`: Busca por nome, slug ou caminho completo
    - `level`: Filtrar por nível hierárquico
    - `menu_type`: Filtrar por tipo de menu
    
    **Paginação:**
    - `skip`: Número de registros para pular
    - `limit`: Máximo de registros (1-1000)
    """,
    responses={
        200: {"description": "Lista de menus retornada com sucesso"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menus(
    skip: int = Query(0, ge=0, description="Paginação: registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: máximo de registros"),
    parent_id: Optional[int] = Query(None, description="Filtrar por menu pai (None = raiz)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Busca por nome/slug/caminho"),
    level: Optional[int] = Query(None, ge=0, le=4, description="Filtrar por nível (0-4)"),
    menu_type: Optional[str] = Query(None, description="Filtrar por tipo de menu"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Listar menus com cache e otimizações"""
    
    try:
        # Buscar menus
        menus = await repository.get_all(
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            status=status,
            search=search,
            level=level
        )
        
        # Contar total para paginação
        total = await repository.count_total(parent_id, status, search)
        
        # Converter entities para schemas
        menu_schemas = []
        for menu in menus:
            schema = MenuListSchema(
                id=menu.id,
                parent_id=menu.parent_id,
                name=menu.name,
                slug=menu.slug,
                level=menu.level,
                sort_order=menu.sort_order,
                menu_type=menu.menu_type,
                status=menu.status,
                is_visible=menu.is_visible,
                visible_in_menu=menu.visible_in_menu,
                permission_name=menu.permission_name,
                has_children=menu.has_children(),
                children_count=len(menu.children),
                full_path_name=menu.full_path_name,
                icon=menu.icon,
                badge_text=menu.badge_text,
                badge_color=menu.badge_color,
                created_at=menu.created_at,
                updated_at=menu.updated_at,
                created_by=menu.created_by,
                updated_by=menu.updated_by
            )
            menu_schemas.append(schema)
        
        # Calcular paginação
        page = (skip // limit) + 1
        has_next = skip + limit < total
        has_prev = skip > 0
        
        logger.info("Menus listados via API", 
                   count=len(menus),
                   total=total,
                   user_id=current_user.id,
                   filters={'parent_id': parent_id, 'status': status, 'level': level})
        
        return MenuListResponse(
            data=menu_schemas,
            total=total,
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        handle_menu_exceptions(e, "get_menus", user_id=current_user.id)


@router.get(
    "/tree",
    response_model=MenuTreeResponseSchema,
    summary="Buscar Árvore Hierárquica",
    description="""
    Retorna a árvore completa de menus em formato hierárquico.
    
    **Performance:**
    - Query recursiva otimizada (CTE)
    - Cache com TTL 5 minutos
    - Máximo 5 níveis de profundidade
    - Métricas de performance incluídas
    
    **Funcionalidades:**
    - Estrutura parent-children completa
    - Ordenação automática por nível e sort_order
    - Apenas menus ativos e visíveis
    - Contexto multi-tenant
    - Cache hit/miss detection
    """,
    responses={
        200: {"description": "Árvore retornada com sucesso"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu_tree(
    context_type: str = Query("system", description="Contexto (system/company/establishment)"),
    context_id: Optional[int] = Query(None, description="ID do contexto específico"),
    include_inactive: bool = Query(False, description="Incluir menus inativos"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Buscar árvore hierárquica completa"""
    
    try:
        use_case = GetMenuTreeUseCase(repository)
        result = await use_case.execute(
            user_id=current_user.id,
            context_type=context_type,
            context_id=context_id,
            include_inactive=include_inactive
        )
        
        logger.info("Árvore de menus obtida via API",
                   total_menus=result.total_menus,
                   cache_hit=result.cache_hit,
                   user_id=current_user.id)
        
        return result
        
    except Exception as e:
        handle_menu_exceptions(e, "get_menu_tree", user_id=current_user.id)


@router.get(
    "/{menu_id}",
    response_model=MenuDetailedSchema,
    summary="Buscar Menu por ID",
    description="""
    Retorna dados completos de um menu específico.
    
    **Inclui:**
    - Todos os campos do menu
    - Informações da hierarquia (parent, children count)
    - Metadados de auditoria
    - Path completo na hierarquia
    
    **Performance:**
    - Cache automático do item (TTL 30 minutos)
    - Busca otimizada por índice primário
    """,
    responses={
        200: {"description": "Menu encontrado"},
        404: {"description": "Menu não encontrado"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu(
    menu_id: int,
    include_relationships: bool = Query(False, description="Incluir parent/children/siblings"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Buscar menu por ID"""
    
    try:
        menu = await repository.get_by_id(menu_id)
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        # Buscar relacionamentos se solicitado
        parent = None
        children = []
        siblings = []
        
        if include_relationships:
            if menu.parent_id:
                parent = await repository.get_by_id(menu.parent_id)
            children = await repository.get_children(menu_id)
            siblings = await repository.get_siblings(menu.parent_id)
        
        # Converter para schema
        schema = MenuDetailedSchema(
            id=menu.id,
            parent_id=menu.parent_id,
            name=menu.name,
            slug=menu.slug,
            url=menu.url,
            route_name=menu.route_name,
            route_params=menu.route_params,
            level=menu.level,
            sort_order=menu.sort_order,
            menu_type=menu.menu_type,
            status=menu.status,
            is_visible=menu.is_visible,
            visible_in_menu=menu.visible_in_menu,
            permission_name=menu.permission_name,
            company_specific=menu.company_specific,
            establishment_specific=menu.establishment_specific,
            icon=menu.icon,
            badge_text=menu.badge_text,
            badge_color=menu.badge_color,
            css_class=menu.css_class,
            description=menu.description,
            help_text=menu.help_text,
            keywords=menu.keywords,
            full_path_name=menu.full_path_name,
            id_path=menu.id_path,
            has_children=menu.has_children(),
            children_count=len(children) if include_relationships else len(menu.children),
            created_at=menu.created_at,
            updated_at=menu.updated_at,
            deleted_at=menu.deleted_at,
            created_by=menu.created_by,
            updated_by=menu.updated_by
        )
        
        logger.info("Menu obtido via API", menu_id=menu_id, user_id=current_user.id)
        
        return schema
        
    except HTTPException:
        raise
    except Exception as e:
        handle_menu_exceptions(e, "get_menu", menu_id=menu_id, user_id=current_user.id)


@router.put(
    "/{menu_id}",
    response_model=MenuDetailedSchema,
    summary="Atualizar Menu",
    description="""
    Atualiza dados de um menu existente.
    
    **Funcionalidades:**
    - Validação de hierarquia (não pode criar loops)
    - Recálculo automático de níveis se mudou parent
    - Atualização de caminhos hierárquicos
    - Invalidação automática de cache
    
    **Restrições:**
    - Menu não pode ser pai de si mesmo
    - Não pode criar loops na hierarquia
    - Slug deve continuar único no nível
    - Máximo 5 níveis de profundidade
    """,
    responses={
        200: {"description": "Menu atualizado com sucesso"},
        400: {"description": "Dados inválidos"},
        404: {"description": "Menu não encontrado"},
        401: {"description": "Não autorizado"}
    }
)
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdateSchema,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Atualizar menu com validações"""
    
    try:
        # Converter schema para DTO
        update_dto = MenuUpdateDTO(
            parent_id=menu_data.parent_id,
            name=menu_data.name,
            slug=menu_data.slug,
            url=menu_data.url,
            route_name=menu_data.route_name,
            route_params=menu_data.route_params,
            icon=menu_data.icon,
            menu_type=menu_data.menu_type,
            status=menu_data.status,
            permission_name=menu_data.permission_name,
            company_specific=menu_data.company_specific,
            establishment_specific=menu_data.establishment_specific,
            badge_text=menu_data.badge_text,
            badge_color=menu_data.badge_color,
            css_class=menu_data.css_class,
            description=menu_data.description,
            help_text=menu_data.help_text,
            keywords=menu_data.keywords,
            is_visible=menu_data.is_visible,
            visible_in_menu=menu_data.visible_in_menu,
            sort_order=menu_data.sort_order
        )
        
        # Executar use case
        use_case = UpdateMenuUseCase(repository)
        result = await use_case.execute(menu_id, update_dto, current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        logger.info("Menu atualizado via API",
                   menu_id=menu_id,
                   updated_by=current_user.id)
        
        # Converter entity para schema
        return MenuDetailedSchema(
            id=result.id,
            parent_id=result.parent_id,
            name=result.name,
            slug=result.slug,
            url=result.url,
            route_name=result.route_name,
            route_params=result.route_params,
            level=result.level,
            sort_order=result.sort_order,
            menu_type=result.menu_type,
            status=result.status,
            is_visible=result.is_visible,
            visible_in_menu=result.visible_in_menu,
            permission_name=result.permission_name,
            company_specific=result.company_specific,
            establishment_specific=result.establishment_specific,
            icon=result.icon,
            badge_text=result.badge_text,
            badge_color=result.badge_color,
            css_class=result.css_class,
            description=result.description,
            help_text=result.help_text,
            keywords=result.keywords,
            full_path_name=result.full_path_name,
            id_path=result.id_path,
            has_children=result.has_children(),
            children_count=len(result.children),
            created_at=result.created_at,
            updated_at=result.updated_at,
            created_by=result.created_by,
            updated_by=result.updated_by
        )
        
    except HTTPException:
        raise
    except (MenuValidationException, MenuHierarchyException, MenuUseCaseException) as e:
        handle_menu_exceptions(e, "update_menu", menu_id=menu_id, user_id=current_user.id)


@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Menu",
    description="""
    Exclui um menu do sistema (soft delete).
    
    **Comportamento:**
    - Exclusão lógica (soft delete)
    - Menu não aparece mais nas listagens
    - Filhos não são excluídos automaticamente
    - Ação auditada nos logs
    
    **Regras de negócio:**
    - Menu com filhos ativos não pode ser excluído
    - Apenas o criador ou admin pode excluir
    - Invalidação automática de cache
    """,
    responses={
        204: {"description": "Menu excluído com sucesso"},
        400: {"description": "Menu possui filhos ativos"},
        404: {"description": "Menu não encontrado"},
        403: {"description": "Sem permissão para excluir"},
        401: {"description": "Não autorizado"}
    }
)
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Excluir menu (soft delete)"""
    
    try:
        use_case = DeleteMenuUseCase(repository)
        success = await use_case.execute(menu_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        logger.info("Menu excluído via API",
                   menu_id=menu_id,
                   deleted_by=current_user.id)
        
    except HTTPException:
        raise
    except (MenuValidationException, MenuUseCaseException) as e:
        handle_menu_exceptions(e, "delete_menu", menu_id=menu_id, user_id=current_user.id)


@router.post(
    "/reorder",
    response_model=MenuOperationResultSchema,
    summary="Reordenar Menus",
    description="""
    Reordena menus irmãos em lote.
    
    **Funcionalidades:**
    - Atualização em batch para performance
    - Validação de integridade
    - Invalidação automática de cache
    - Validação de menus irmãos
    
    **Payload:**
    ```json
    {
        "parent_id": null,
        "menu_orders": [
            {"menu_id": 1, "sort_order": 1},
            {"menu_id": 2, "sort_order": 2}
        ]
    }
    ```
    """,
    responses={
        200: {"description": "Reordenação concluída com sucesso"},
        400: {"description": "Dados inválidos"},
        401: {"description": "Não autorizado"}
    }
)
async def reorder_menus(
    reorder_data: ReorderRequestSchema,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Reordenar menus irmãos"""
    
    try:
        # Converter schema para DTO
        reorder_dto = ReorderRequestDTO(
            parent_id=reorder_data.parent_id,
            menu_orders=reorder_data.menu_orders
        )
        
        use_case = ReorderMenusUseCase(repository)
        success = await use_case.execute(
            reorder_dto.parent_id,
            reorder_dto.menu_orders,
            current_user.id
        )
        
        logger.info("Menus reordenados via API",
                   parent_id=reorder_data.parent_id,
                   count=len(reorder_data.menu_orders),
                   reordered_by=current_user.id)
        
        return MenuOperationResultSchema(
            success=success,
            message="Menus reordenados com sucesso" if success else "Falha na reordenação",
            errors=[],
            warnings=[]
        )
        
    except (MenuValidationException, MenuUseCaseException) as e:
        handle_menu_exceptions(e, "reorder_menus", user_id=current_user.id)


@router.get(
    "/search",
    response_model=MenuSearchResponse,
    summary="Buscar Menus",
    description="""
    Busca textual avançada em menus com scoring de relevância.
    
    **Funcionalidades:**
    - Full-text search otimizada
    - Score de relevância
    - Cache de resultados (TTL 2 minutos)
    - Filtros de contexto
    
    **Algoritmo de relevância:**
    1. Nome exato (100 pontos)
    2. Nome contém no início (90 pontos)
    3. Nome contém (80 pontos)
    4. Slug exato (75 pontos)
    5. Descrição (60 pontos)
    6. Keywords (50 pontos)
    7. Caminho (40 pontos)
    """,
    responses={
        200: {"description": "Resultados da busca"},
        401: {"description": "Não autorizado"}
    }
)
async def search_menus(
    query: str = Query(..., min_length=2, max_length=100, description="Termo de busca"),
    context_type: str = Query("system", description="Contexto da busca"),
    context_id: Optional[int] = Query(None, description="ID do contexto específico"),
    include_inactive: bool = Query(False, description="Incluir menus inativos"),
    limit: int = Query(20, ge=1, le=100, description="Máximo de resultados"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Buscar menus com scoring de relevância"""
    
    start_time = time.time()
    
    try:
        search_request = MenuSearchRequestDTO(
            query=query,
            context_type=context_type,
            context_id=context_id,
            include_inactive=include_inactive,
            limit=limit
        )
        
        use_case = SearchMenusUseCase(repository)
        results = await use_case.execute(search_request)
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info("Busca de menus via API",
                   query=query,
                   results_count=len(results),
                   execution_time_ms=execution_time_ms,
                   user_id=current_user.id)
        
        return MenuSearchResponse(
            data=results,
            query=query,
            total=len(results),
            execution_time_ms=execution_time_ms
        )
        
    except Exception as e:
        handle_menu_exceptions(e, "search_menus", query=query, user_id=current_user.id)


@router.get(
    "/statistics",
    response_model=MenuStatisticsSchema,
    summary="Estatísticas de Menus",
    description="""
    Retorna estatísticas completas do sistema de menus.
    
    **Métricas incluídas:**
    - Totais por status (ativo, inativo, rascunho)
    - Distribuição por nível hierárquico
    - Distribuição por tipo de menu
    - Menus com permissões específicas
    - Menus específicos por contexto
    - Ícones mais utilizados
    - Atividade recente
    
    **Performance:**
    - Cache de 1 hora para estatísticas
    - Queries otimizadas com agregações
    """,
    responses={
        200: {"description": "Estatísticas obtidas com sucesso"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu_statistics(
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Obter estatísticas completas dos menus"""
    
    try:
        use_case = GetMenuStatisticsUseCase(repository)
        stats = await use_case.execute()
        
        logger.info("Estatísticas de menus obtidas via API",
                   total_menus=stats.total_menus,
                   user_id=current_user.id)
        
        return stats
        
    except Exception as e:
        handle_menu_exceptions(e, "get_statistics", user_id=current_user.id)


@router.post(
    "/bulk-update",
    response_model=MenuOperationResultSchema,
    summary="Atualização em Lote",
    description="""
    Atualiza múltiplos menus em uma única operação.
    
    **Operações suportadas:**
    - Alterar status em lote
    - Alterar visibilidade em lote
    - Validação prévia dos IDs
    
    **Funcionalidades:**
    - Transação única para consistência
    - Validação de existência dos menus
    - Invalidação automática de cache
    - Log de auditoria
    """,
    responses={
        200: {"description": "Atualização em lote concluída"},
        400: {"description": "Dados inválidos ou menus não encontrados"},
        401: {"description": "Não autorizado"}
    }
)
async def bulk_update_menus(
    update_request: BulkUpdateRequestSchema,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Atualizar múltiplos menus em lote"""
    
    try:
        bulk_dto = BulkUpdateRequestDTO(
            menu_ids=update_request.menu_ids,
            status=update_request.status,
            is_visible=update_request.is_visible,
            visible_in_menu=update_request.visible_in_menu
        )
        
        use_case = BulkUpdateMenusUseCase(repository)
        result = await use_case.execute(bulk_dto, current_user.id)
        
        logger.info("Atualização em lote via API",
                   menu_count=len(update_request.menu_ids),
                   success=result.success,
                   user_id=current_user.id)
        
        return result
        
    except Exception as e:
        handle_menu_exceptions(e, "bulk_update", user_id=current_user.id)


@router.get(
    "/health",
    response_model=MenuHealthSchema,
    summary="Health Check do Sistema de Menus",
    description="""
    Verifica a saúde do sistema de menus.
    
    **Verificações:**
    - Status do serviço
    - Status do cache Redis
    - Status do repository/banco
    - Métricas de performance
    - Contadores básicos
    """,
    responses={
        200: {"description": "Status do sistema"},
        503: {"description": "Sistema com problemas"}
    }
)
async def menu_health_check(
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Health check do sistema de menus"""
    
    try:
        # Verificar cache
        cache_service = await get_menu_cache_service()
        cache_stats = await cache_service.get_cache_stats()
        
        # Verificar repository (query simples)
        total_menus = await repository.count_total()
        
        # Métricas básicas de performance
        start_time = time.time()
        test_menus = await repository.get_all(limit=5)
        query_time_ms = int((time.time() - start_time) * 1000)
        
        health_status = "healthy" if cache_stats.get('redis_connected', False) else "degraded"
        
        return MenuHealthSchema(
            service="menu_crud_service",
            status=health_status,
            version="1.0.0",
            cache_status=cache_stats,
            repository_status="connected" if total_menus >= 0 else "error",
            total_menus=total_menus,
            performance_metrics={
                "test_query_time_ms": query_time_ms,
                "cache_connected": cache_stats.get('redis_connected', False)
            }
        )
        
    except Exception as e:
        logger.error("Erro no health check", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sistema com problemas"
        )


@router.get(
    "/{menu_id}/path",
    response_model=MenuPathSchema,
    summary="Obter Caminho do Menu",
    description="""
    Retorna o caminho completo (breadcrumbs) do menu até a raiz.
    
    **Funcionalidades:**
    - Caminho completo da raiz até o menu
    - Útil para breadcrumbs
    - Cache automático
    """,
    responses={
        200: {"description": "Caminho obtido com sucesso"},
        404: {"description": "Menu não encontrado"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu_path(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Obter caminho completo do menu"""
    
    try:
        path = await repository.get_menu_path(menu_id)
        
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        # Converter para breadcrumbs
        breadcrumbs = [
            {
                "id": menu.id,
                "name": menu.name,
                "slug": menu.slug,
                "url": menu.url,
                "level": menu.level
            }
            for menu in path
        ]
        
        return MenuPathSchema(
            menu_id=menu_id,
            breadcrumbs=breadcrumbs,
            total_levels=len(breadcrumbs)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_menu_exceptions(e, "get_menu_path", menu_id=menu_id, user_id=current_user.id)