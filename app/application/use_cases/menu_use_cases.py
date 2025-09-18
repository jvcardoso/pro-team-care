"""
Menu Use Cases - Application Layer
Casos de uso principais para operações com menus dinâmicos
"""

import time
from typing import Dict, List, Optional

import structlog

from app.application.dto.menu_dto import (
    BulkUpdateRequestDTO,
    MenuCreateDTO,
    MenuOperationResultDTO,
    MenuSearchRequestDTO,
    MenuSearchResultDTO,
    MenuStatisticsDTO,
    MenuTreeItemDTO,
    MenuTreeResponseDTO,
    MenuUpdateDTO,
)
from app.domain.entities.menu import MenuEntity, MenuStatus
from app.domain.repositories.menu_repository_interface import MenuRepositoryInterface

logger = structlog.get_logger()


class MenuUseCaseException(Exception):
    """Exception base para casos de uso de menu"""


class MenuValidationException(MenuUseCaseException):
    """Exception para erros de validação"""


class MenuHierarchyException(MenuUseCaseException):
    """Exception para erros de hierarquia"""


class CreateMenuUseCase:
    """Caso de uso: Criar Menu"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(self, data: MenuCreateDTO, created_by: int) -> MenuEntity:
        """
        Executar criação de menu com validações de negócio

        Args:
            data: Dados do menu a ser criado
            created_by: ID do usuário que está criando

        Returns:
            MenuEntity: Menu criado

        Raises:
            MenuValidationException: Se dados inválidos
            MenuHierarchyException: Se hierarquia inválida
        """

        start_time = time.time()

        try:
            # Validação: slug único no nível
            existing = await self.repository.get_by_slug(data.slug, data.parent_id)
            if existing:
                raise MenuValidationException(
                    f"Menu com slug '{data.slug}' já existe no nível"
                )

            # Validação: hierarquia (máximo 5 níveis)
            level = 0
            if data.parent_id:
                parent = await self.repository.get_by_id(data.parent_id)
                if not parent:
                    raise MenuValidationException("Menu pai não encontrado")

                if parent.level >= 4:
                    raise MenuHierarchyException(
                        "Máximo de 5 níveis de hierarquia permitidos"
                    )

                level = parent.level + 1

                # Validar se pai pode ter filhos
                if not parent.can_have_children():
                    raise MenuHierarchyException(
                        f"Menu pai do tipo '{parent.menu_type}' não pode ter filhos"
                    )

            # Criar entidade
            menu_entity = MenuEntity(
                parent_id=data.parent_id,
                name=data.name,
                slug=data.slug,
                url=data.url,
                route_name=data.route_name,
                route_params=data.route_params,
                icon=data.icon,
                level=level,
                sort_order=0,  # Será calculado no repository
                menu_type=data.menu_type,
                status=MenuStatus.ACTIVE,
                is_visible=data.is_visible,
                visible_in_menu=data.visible_in_menu,
                permission_name=data.permission_name,
                company_specific=data.company_specific,
                establishment_specific=data.establishment_specific,
                badge_text=data.badge_text,
                badge_color=data.badge_color,
                css_class=data.css_class,
                description=data.description,
                help_text=data.help_text,
                keywords=data.keywords,
                created_by=created_by,
            )

            # Validar regras de negócio
            validation_errors = menu_entity.validate_hierarchy_rules()
            if validation_errors:
                raise MenuValidationException(
                    f"Erros de validação: {', '.join(validation_errors)}"
                )

            # Criar no repository
            result = await self.repository.create(menu_entity)

            execution_time = time.time() - start_time
            self.logger.info(
                "Menu criado com sucesso",
                menu_id=result.id,
                name=result.name,
                level=result.level,
                created_by=created_by,
                execution_time=f"{execution_time:.3f}s",
            )

            return result

        except (MenuValidationException, MenuHierarchyException):
            raise
        except Exception as e:
            self.logger.error(
                "Erro interno na criação de menu", error=str(e), created_by=created_by
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")


class UpdateMenuUseCase:
    """Caso de uso: Atualizar Menu"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(
        self, menu_id: int, data: MenuUpdateDTO, updated_by: int
    ) -> Optional[MenuEntity]:
        """
        Executar atualização com validações

        Args:
            menu_id: ID do menu a ser atualizado
            data: Dados de atualização
            updated_by: ID do usuário que está atualizando

        Returns:
            MenuEntity atualizado ou None se não encontrado

        Raises:
            MenuValidationException: Se dados inválidos
            MenuHierarchyException: Se hierarquia inválida
        """

        start_time = time.time()

        try:
            # Buscar menu existente
            existing = await self.repository.get_by_id(menu_id)
            if not existing:
                return None

            # Validação: não pode ser pai de si mesmo
            if data.parent_id == menu_id:
                raise MenuHierarchyException("Menu não pode ser pai de si mesmo")

            # Validação: slug único no nível (se mudou)
            if data.slug and data.slug != existing.slug:
                parent_id = (
                    data.parent_id if data.parent_id is not None else existing.parent_id
                )
                existing_with_slug = await self.repository.get_by_slug(
                    data.slug, parent_id
                )
                if existing_with_slug and existing_with_slug.id != menu_id:
                    raise MenuValidationException(
                        f"Menu com slug '{data.slug}' já existe no nível"
                    )

            # Validação: mudança de hierarquia
            if data.parent_id is not None and data.parent_id != existing.parent_id:
                if not await self.repository.validate_hierarchy_change(
                    menu_id, data.parent_id
                ):
                    raise MenuHierarchyException("Alteração criaria loop na hierarquia")

                # Verificar nível máximo
                if data.parent_id:
                    parent = await self.repository.get_by_id(data.parent_id)
                    if parent and parent.level >= 4:
                        raise MenuHierarchyException(
                            "Máximo de 5 níveis de hierarquia permitidos"
                        )

            # Aplicar mudanças na entidade existente
            updated_fields = []
            for field, value in data.model_dump(exclude_unset=True).items():
                if hasattr(existing, field) and getattr(existing, field) != value:
                    setattr(existing, field, value)
                    updated_fields.append(field)

            existing.updated_by = updated_by

            # Validar regras de negócio após mudanças
            validation_errors = existing.validate_hierarchy_rules()
            if validation_errors:
                raise MenuValidationException(
                    f"Erros de validação: {', '.join(validation_errors)}"
                )

            # Atualizar no repository
            result = await self.repository.update(menu_id, existing)

            execution_time = time.time() - start_time
            self.logger.info(
                "Menu atualizado com sucesso",
                menu_id=menu_id,
                updated_fields=updated_fields,
                updated_by=updated_by,
                execution_time=f"{execution_time:.3f}s",
            )

            return result

        except (MenuValidationException, MenuHierarchyException):
            raise
        except Exception as e:
            self.logger.error(
                "Erro interno na atualização de menu",
                menu_id=menu_id,
                error=str(e),
                updated_by=updated_by,
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")


class DeleteMenuUseCase:
    """Caso de uso: Excluir Menu"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(self, menu_id: int, deleted_by: int) -> bool:
        """
        Executar exclusão com validações

        Args:
            menu_id: ID do menu a ser excluído
            deleted_by: ID do usuário que está excluindo

        Returns:
            bool: True se excluído com sucesso

        Raises:
            MenuValidationException: Se menu tem filhos ativos
        """

        start_time = time.time()

        try:
            # Verificar se menu existe
            menu = await self.repository.get_by_id(menu_id)
            if not menu:
                return False

            # Verificar se tem filhos ativos
            children = await self.repository.get_children(menu_id)
            if children:
                active_children = [c for c in children if c.status == MenuStatus.ACTIVE]
                if active_children:
                    raise MenuValidationException(
                        f"Menu possui {len(active_children)} filhos ativos. "
                        "Remova ou desative os filhos primeiro."
                    )

            # Executar exclusão
            success = await self.repository.delete(menu_id)

            execution_time = time.time() - start_time

            if success:
                self.logger.info(
                    "Menu excluído com sucesso",
                    menu_id=menu_id,
                    name=menu.name,
                    deleted_by=deleted_by,
                    execution_time=f"{execution_time:.3f}s",
                )
            else:
                self.logger.warning(
                    "Falha na exclusão do menu", menu_id=menu_id, deleted_by=deleted_by
                )

            return success

        except MenuValidationException:
            raise
        except Exception as e:
            self.logger.error(
                "Erro interno na exclusão de menu",
                menu_id=menu_id,
                error=str(e),
                deleted_by=deleted_by,
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")


class GetMenuTreeUseCase:
    """Caso de uso: Buscar Árvore de Menus (com cache)"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(
        self,
        user_id: Optional[int] = None,
        context_type: str = "system",
        context_id: Optional[int] = None,
        include_inactive: bool = False,
    ) -> MenuTreeResponseDTO:
        """
        Buscar árvore com cache inteligente e métricas

        Args:
            user_id: ID do usuário (para cache e permissões)
            context_type: Tipo de contexto
            context_id: ID do contexto específico
            include_inactive: Incluir menus inativos

        Returns:
            MenuTreeResponseDTO: Árvore com metadados
        """

        start_time = time.time()

        try:
            # Buscar árvore do repository (com cache automático)
            tree = await self.repository.get_hierarchy_tree(
                user_id=user_id,
                context_type=context_type,
                include_inactive=include_inactive,
            )

            # Converter para DTOs
            tree_items = []
            total_menus = 0
            max_depth = 0

            for menu in tree:
                tree_item = self._convert_to_tree_item(menu)
                tree_items.append(tree_item)

                # Calcular estatísticas
                menu_count, depth = self._count_tree_stats(menu)
                total_menus += menu_count
                max_depth = max(max_depth, depth)

            execution_time = time.time() - start_time
            load_time_ms = int(execution_time * 1000)

            # Determinar se foi cache hit (heurística baseada no tempo)
            cache_hit = execution_time < 0.05  # Menos de 50ms = provavelmente cache

            result = MenuTreeResponseDTO(
                user_id=user_id,
                context_type=context_type,
                context_id=context_id,
                total_menus=total_menus,
                root_menus=len(tree),
                max_depth=max_depth,
                tree=tree_items,
                cache_hit=cache_hit,
                load_time_ms=load_time_ms,
            )

            self.logger.info(
                "Árvore de menus carregada",
                user_id=user_id,
                context_type=context_type,
                total_menus=total_menus,
                root_menus=len(tree),
                cache_hit=cache_hit,
                execution_time=f"{execution_time:.3f}s",
            )

            return result

        except Exception as e:
            self.logger.error(
                "Erro ao buscar árvore de menus",
                user_id=user_id,
                context_type=context_type,
                error=str(e),
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")

    def _convert_to_tree_item(self, menu: MenuEntity) -> MenuTreeItemDTO:
        """Converter MenuEntity para MenuTreeItemDTO"""
        return MenuTreeItemDTO(
            id=menu.id,
            parent_id=menu.parent_id,
            name=menu.name,
            slug=menu.slug,
            url=menu.url,
            icon=menu.icon,
            level=menu.level,
            sort_order=menu.sort_order,
            menu_type=menu.menu_type,
            badge_text=menu.badge_text,
            badge_color=menu.badge_color,
            has_permission=True,  # TODO: Implementar lógica de permissões
            is_accessible=True,  # TODO: Implementar lógica de contexto
            children=[self._convert_to_tree_item(child) for child in menu.children],
        )

    def _count_tree_stats(self, menu: MenuEntity) -> tuple[int, int]:
        """Contar nós e profundidade máxima recursivamente"""
        count = 1
        max_depth = menu.level

        for child in menu.children:
            child_count, child_depth = self._count_tree_stats(child)
            count += child_count
            max_depth = max(max_depth, child_depth)

        return count, max_depth


class ReorderMenusUseCase:
    """Caso de uso: Reordenar Menus"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(
        self,
        parent_id: Optional[int],
        menu_orders: List[Dict[str, int]],
        reordered_by: int,
    ) -> bool:
        """
        Executar reordenação com validações

        Args:
            parent_id: ID do menu pai (None = raiz)
            menu_orders: Lista de {'menu_id': int, 'sort_order': int}
            reordered_by: ID do usuário que está reordenando

        Returns:
            bool: True se reordenação bem-sucedida

        Raises:
            MenuValidationException: Se dados inválidos
        """

        start_time = time.time()

        try:
            # Validar que todos os menus existem e são irmãos
            siblings = await self.repository.get_siblings(parent_id)
            sibling_ids = {menu.id for menu in siblings}

            menu_ids_to_reorder = {item["menu_id"] for item in menu_orders}

            # Verificar se todos os IDs são válidos
            invalid_ids = menu_ids_to_reorder - sibling_ids
            if invalid_ids:
                raise MenuValidationException(
                    f"Menus não encontrados ou não são irmãos: {invalid_ids}"
                )

            # Validar se não há sort_orders duplicados
            sort_orders = [item["sort_order"] for item in menu_orders]
            if len(sort_orders) != len(set(sort_orders)):
                raise MenuValidationException(
                    "Sort orders duplicados não são permitidos"
                )

            # Executar reordenação
            success = await self.repository.reorder_siblings(parent_id, menu_orders)

            execution_time = time.time() - start_time

            if success:
                self.logger.info(
                    "Menus reordenados com sucesso",
                    parent_id=parent_id,
                    count=len(menu_orders),
                    reordered_by=reordered_by,
                    execution_time=f"{execution_time:.3f}s",
                )
            else:
                self.logger.warning(
                    "Falha na reordenação dos menus",
                    parent_id=parent_id,
                    reordered_by=reordered_by,
                )

            return success

        except MenuValidationException:
            raise
        except Exception as e:
            self.logger.error(
                "Erro interno na reordenação de menus",
                parent_id=parent_id,
                error=str(e),
                reordered_by=reordered_by,
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")


class SearchMenusUseCase:
    """Caso de uso: Buscar Menus"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(self, request: MenuSearchRequestDTO) -> List[MenuSearchResultDTO]:
        """
        Executar busca com cache e scoring

        Args:
            request: Parâmetros de busca

        Returns:
            Lista de resultados com score de relevância
        """

        start_time = time.time()

        try:
            # Buscar menus (com cache automático)
            menus = await self.repository.search_menus(
                query=request.query,
                user_id=None,  # TODO: Implementar filtro por usuário
                context_type=request.context_type,
                limit=request.limit,
            )

            # Converter para DTOs com scoring
            results = []
            for menu in menus:
                score, reason = self._calculate_relevance_score(menu, request.query)

                result = MenuSearchResultDTO(
                    id=menu.id,
                    name=menu.name,
                    slug=menu.slug,
                    url=menu.url,
                    full_path_name=menu.full_path_name,
                    description=menu.description,
                    icon=menu.icon,
                    level=menu.level,
                    menu_type=menu.menu_type,
                    status=menu.status,
                    match_score=score,
                    match_reason=reason,
                )
                results.append(result)

            # Ordenar por relevância
            results.sort(key=lambda x: x.match_score, reverse=True)

            execution_time = time.time() - start_time

            self.logger.info(
                "Busca de menus realizada",
                query=request.query,
                results_count=len(results),
                execution_time=f"{execution_time:.3f}s",
            )

            return results

        except Exception as e:
            self.logger.error(
                "Erro na busca de menus", query=request.query, error=str(e)
            )
            raise MenuUseCaseException(f"Erro interno: {str(e)}")

    def _calculate_relevance_score(
        self, menu: MenuEntity, query: str
    ) -> tuple[float, str]:
        """Calcular score de relevância e razão do match"""
        query_lower = query.lower()

        # Nome exato
        if menu.name.lower() == query_lower:
            return 100.0, "nome_exato"

        # Nome contém (início)
        if menu.name.lower().startswith(query_lower):
            return 90.0, "nome_inicio"

        # Nome contém
        if query_lower in menu.name.lower():
            return 80.0, "nome_contem"

        # Slug exato
        if menu.slug.lower() == query_lower:
            return 75.0, "slug_exato"

        # Slug contém
        if query_lower in menu.slug.lower():
            return 70.0, "slug_contem"

        # Descrição contém
        if menu.description and query_lower in menu.description.lower():
            return 60.0, "descricao"

        # Keywords
        if menu.keywords:
            for keyword in menu.keywords:
                if query_lower in keyword.lower():
                    return 50.0, "keyword"

        # Path contém
        if menu.full_path_name and query_lower in menu.full_path_name.lower():
            return 40.0, "caminho"

        return 10.0, "outro"


class GetMenuStatisticsUseCase:
    """Caso de uso: Obter Estatísticas de Menus"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(self) -> MenuStatisticsDTO:
        """
        Obter estatísticas completas dos menus

        Returns:
            MenuStatisticsDTO: Estatísticas detalhadas
        """

        start_time = time.time()

        try:
            # Buscar estatísticas do repository
            stats = await self.repository.get_menu_statistics()

            # TODO: Implementar mais estatísticas (ícones mais usados, atividade recente)
            most_used_icons = []
            recent_activity = {
                "created_today": 0,
                "updated_today": 0,
                "created_week": 0,
                "updated_week": 0,
            }

            result = MenuStatisticsDTO(
                total_menus=stats["total_menus"],
                active_menus=stats["active_menus"],
                inactive_menus=stats["inactive_menus"],
                draft_menus=stats["draft_menus"],
                menus_by_level=stats["menus_by_level"],
                menus_by_type=stats["menus_by_type"],
                menus_with_permissions=stats["menus_with_permissions"],
                company_specific_menus=stats["company_specific_menus"],
                establishment_specific_menus=stats["establishment_specific_menus"],
                root_menus=stats["root_menus"],
                max_depth=stats["max_depth"],
                avg_children_per_menu=stats["avg_children_per_menu"],
                most_used_icons=most_used_icons,
                recent_activity=recent_activity,
            )

            execution_time = time.time() - start_time

            self.logger.info(
                "Estatísticas de menus obtidas",
                total_menus=result.total_menus,
                execution_time=f"{execution_time:.3f}s",
            )

            return result

        except Exception as e:
            self.logger.error("Erro ao obter estatísticas de menus", error=str(e))
            raise MenuUseCaseException(f"Erro interno: {str(e)}")


class BulkUpdateMenusUseCase:
    """Caso de uso: Atualização em Lote"""

    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
        self.logger = logger

    async def execute(
        self, request: BulkUpdateRequestDTO, updated_by: int
    ) -> MenuOperationResultDTO:
        """
        Executar atualização em lote

        Args:
            request: Parâmetros da atualização
            updated_by: ID do usuário que está atualizando

        Returns:
            MenuOperationResultDTO: Resultado da operação
        """

        start_time = time.time()

        try:
            # Verificar se todos os menus existem
            errors = []
            warnings = []

            for menu_id in request.menu_ids:
                menu = await self.repository.get_by_id(menu_id)
                if not menu:
                    errors.append(f"Menu {menu_id} não encontrado")
                elif (
                    menu.status == MenuStatus.INACTIVE
                    and request.status == MenuStatus.INACTIVE
                ):
                    warnings.append(f"Menu {menu_id} já está inativo")

            if errors:
                return MenuOperationResultDTO(
                    success=False,
                    message="Erros de validação encontrados",
                    errors=[
                        {"field": "menu_ids", "message": error, "code": "NOT_FOUND"}
                        for error in errors
                    ],
                    warnings=warnings,
                )

            # Executar atualização
            success = False
            if request.status:
                success = await self.repository.bulk_update_status(
                    request.menu_ids, request.status.value
                )

            execution_time = time.time() - start_time

            result = MenuOperationResultDTO(
                success=success,
                message=f"Atualização em lote {'realizada' if success else 'falhou'}",
                errors=[],
                warnings=warnings,
            )

            if success:
                self.logger.info(
                    "Atualização em lote realizada",
                    menu_count=len(request.menu_ids),
                    status=request.status.value if request.status else None,
                    updated_by=updated_by,
                    execution_time=f"{execution_time:.3f}s",
                )

            return result

        except Exception as e:
            self.logger.error(
                "Erro na atualização em lote",
                menu_ids=request.menu_ids,
                error=str(e),
                updated_by=updated_by,
            )

            return MenuOperationResultDTO(
                success=False,
                message="Erro interno na atualização",
                errors=[
                    {"field": "system", "message": str(e), "code": "INTERNAL_ERROR"}
                ],
                warnings=[],
            )
