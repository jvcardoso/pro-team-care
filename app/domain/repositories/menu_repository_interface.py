"""
Menu Repository Interface - Domain Layer
Interface para Repository de Menus seguindo Dependency Inversion Principle
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.entities.menu import MenuEntity


class MenuRepositoryInterface(ABC):
    """
    Interface para Repository de Menus (Dependency Inversion)

    Define o contrato que deve ser implementado pelos repositories
    concretos na camada de infraestrutura. Esta interface permite
    que a camada de domínio não dependa de implementações específicas.
    """

    @abstractmethod
    async def create(self, menu: MenuEntity) -> MenuEntity:
        """
        Criar novo menu

        Args:
            menu: Entidade do menu a ser criado

        Returns:
            MenuEntity: Menu criado com ID preenchido

        Raises:
            ValueError: Se dados inválidos
            DuplicateSlugError: Se slug já existe no nível
        """

    @abstractmethod
    async def get_by_id(self, menu_id: int) -> Optional[MenuEntity]:
        """
        Buscar menu por ID

        Args:
            menu_id: ID do menu

        Returns:
            MenuEntity ou None se não encontrado
        """

    @abstractmethod
    async def get_by_slug(
        self, slug: str, parent_id: Optional[int] = None
    ) -> Optional[MenuEntity]:
        """
        Buscar menu por slug no nível específico

        Args:
            slug: Slug do menu
            parent_id: ID do menu pai (None = raiz)

        Returns:
            MenuEntity ou None se não encontrado
        """

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        level: Optional[int] = None,
    ) -> List[MenuEntity]:
        """
        Listar menus com filtros e paginação

        Args:
            skip: Registros para pular (paginação)
            limit: Máximo de registros para retornar
            parent_id: Filtrar por menu pai (None = raiz)
            status: Filtrar por status
            search: Buscar por nome, slug ou caminho
            level: Filtrar por nível hierárquico

        Returns:
            Lista de menus
        """

    @abstractmethod
    async def update(self, menu_id: int, menu: MenuEntity) -> Optional[MenuEntity]:
        """
        Atualizar menu existente

        Args:
            menu_id: ID do menu a ser atualizado
            menu: Dados atualizados do menu

        Returns:
            MenuEntity atualizado ou None se não encontrado

        Raises:
            ValueError: Se dados inválidos
            HierarchyError: Se mudança de hierarquia é inválida
        """

    @abstractmethod
    async def delete(self, menu_id: int) -> bool:
        """
        Excluir menu (soft delete)

        Args:
            menu_id: ID do menu a ser excluído

        Returns:
            bool: True se excluído com sucesso

        Raises:
            ValueError: Se menu tem filhos ativos
        """

    @abstractmethod
    async def get_hierarchy_tree(
        self,
        user_id: Optional[int] = None,
        context_type: str = "system",
        include_inactive: bool = False,
    ) -> List[MenuEntity]:
        """
        Buscar árvore hierárquica completa de menus

        Args:
            user_id: ID do usuário (para filtro de permissões)
            context_type: Contexto (system/company/establishment)
            include_inactive: Incluir menus inativos

        Returns:
            Lista de menus raiz com filhos aninhados
        """

    @abstractmethod
    async def get_siblings(self, parent_id: Optional[int]) -> List[MenuEntity]:
        """
        Buscar menus irmãos (mesmo nível)

        Args:
            parent_id: ID do menu pai (None = raiz)

        Returns:
            Lista de menus no mesmo nível
        """

    @abstractmethod
    async def reorder_siblings(
        self, parent_id: Optional[int], menu_orders: List[Dict]
    ) -> bool:
        """
        Reordenar menus irmãos em lote

        Args:
            parent_id: ID do menu pai (None = raiz)
            menu_orders: Lista de {'menu_id': int, 'sort_order': int}

        Returns:
            bool: True se reordenação bem-sucedida
        """

    @abstractmethod
    async def validate_hierarchy_change(
        self, menu_id: int, new_parent_id: Optional[int]
    ) -> bool:
        """
        Validar se mudança de hierarquia é válida (não cria loops)

        Args:
            menu_id: ID do menu sendo movido
            new_parent_id: Novo menu pai

        Returns:
            bool: True se mudança é válida
        """

    @abstractmethod
    async def get_children(
        self, parent_id: int, recursive: bool = False
    ) -> List[MenuEntity]:
        """
        Buscar filhos de um menu

        Args:
            parent_id: ID do menu pai
            recursive: Se deve buscar todos os descendentes

        Returns:
            Lista de menus filhos
        """

    @abstractmethod
    async def count_total(
        self,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        """
        Contar total de menus com filtros

        Args:
            parent_id: Filtrar por menu pai
            status: Filtrar por status
            search: Busca por texto

        Returns:
            int: Total de menus
        """

    @abstractmethod
    async def get_user_accessible_menus(
        self,
        user_id: int,
        context_type: str = "system",
        context_id: Optional[int] = None,
    ) -> List[MenuEntity]:
        """
        Buscar menus acessíveis para usuário específico
        (considerando permissões e contexto)

        Args:
            user_id: ID do usuário
            context_type: Tipo de contexto
            context_id: ID do contexto específico

        Returns:
            Lista de menus acessíveis
        """

    @abstractmethod
    async def get_menu_path(self, menu_id: int) -> List[MenuEntity]:
        """
        Buscar caminho completo do menu até a raiz

        Args:
            menu_id: ID do menu

        Returns:
            Lista de menus do caminho (raiz até o menu)
        """

    @abstractmethod
    async def search_menus(
        self,
        query: str,
        user_id: Optional[int] = None,
        context_type: str = "system",
        limit: int = 50,
    ) -> List[MenuEntity]:
        """
        Busca textual em menus

        Args:
            query: Termo de busca
            user_id: ID do usuário (para filtro de permissões)
            context_type: Contexto da busca
            limit: Máximo de resultados

        Returns:
            Lista de menus encontrados
        """

    @abstractmethod
    async def get_menu_statistics(self) -> Dict[str, Any]:
        """
        Buscar estatísticas dos menus

        Returns:
            Dict com estatísticas (total, por nível, por tipo, etc.)
        """

    @abstractmethod
    async def bulk_update_status(self, menu_ids: List[int], status: str) -> bool:
        """
        Atualizar status de múltiplos menus em lote

        Args:
            menu_ids: Lista de IDs dos menus
            status: Novo status

        Returns:
            bool: True se atualização bem-sucedida
        """

    @abstractmethod
    async def get_recently_modified(
        self, limit: int = 10, user_id: Optional[int] = None
    ) -> List[MenuEntity]:
        """
        Buscar menus modificados recentemente

        Args:
            limit: Máximo de registros
            user_id: Filtrar por usuário que modificou

        Returns:
            Lista de menus ordenados por data de modificação
        """
