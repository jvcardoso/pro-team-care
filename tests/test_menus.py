"""
Testes para o sistema de menus dinâmicos
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.repositories.menu_repository import MenuRepository


class TestMenuRepository:
    """Testes para MenuRepository"""

    @pytest.fixture
    def mock_db(self):
        """Mock do banco de dados"""
        return AsyncMock()

    @pytest.fixture
    def menu_repo(self, mock_db):
        """Instância do MenuRepository com mock"""
        return MenuRepository(mock_db)

    @pytest.mark.asyncio
    async def test_get_menu_tree_empty(self, menu_repo):
        """Testa conversão de lista vazia para árvore"""
        result = await menu_repo.get_menu_tree([])
        assert result == []

    @pytest.mark.asyncio
    async def test_get_menu_tree_single_level(self, menu_repo):
        """Testa conversão de menus de nível único"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Dashboard",
                "level": 0,
                "sort_order": 1,
            },
            {"id": 2, "parent_id": None, "name": "Users", "level": 0, "sort_order": 2},
        ]

        result = await menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 2
        assert result[0]["name"] == "Dashboard"
        assert result[1]["name"] == "Users"
        assert result[0]["children"] == []
        assert result[1]["children"] == []

    @pytest.mark.asyncio
    async def test_get_menu_tree_hierarchy(self, menu_repo):
        """Testa conversão de menus hierárquicos"""
        flat_menus = [
            {"id": 1, "parent_id": None, "name": "Admin", "level": 0, "sort_order": 1},
            {"id": 2, "parent_id": 1, "name": "Users", "level": 1, "sort_order": 1},
            {"id": 3, "parent_id": 1, "name": "Roles", "level": 1, "sort_order": 2},
            {
                "id": 4,
                "parent_id": None,
                "name": "Reports",
                "level": 0,
                "sort_order": 2,
            },
        ]

        result = await menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 2
        admin_menu = result[0]
        assert admin_menu["name"] == "Admin"
        assert len(admin_menu["children"]) == 2
        assert admin_menu["children"][0]["name"] == "Users"
        assert admin_menu["children"][1]["name"] == "Roles"

    @pytest.mark.asyncio
    async def test_get_user_info_not_found(self, menu_repo, mock_db):
        """Testa busca de usuário não encontrado"""
        # Mock da query
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db.execute.return_value = mock_result

        result = await menu_repo.get_user_info(999)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, menu_repo, mock_db):
        """Testa busca de usuário com sucesso"""
        # Mock da query
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            0: 1,  # id
            1: "user@test.com",  # email
            2: False,  # is_system_admin
            3: True,  # is_active
            4: "John Doe",  # name
            5: "person",  # person_type
        }[key]

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_db.execute.return_value = mock_result

        result = await menu_repo.get_user_info(1)

        assert result is not None
        assert result["id"] == 1
        assert result["email"] == "user@test.com"
        assert result["is_system_admin"] is False
        assert result["is_active"] is True
        assert result["name"] == "John Doe"
        assert result["person_type"] == "person"


class TestMenuEndpoints:
    """Testes para endpoints de menus"""

    def test_menu_endpoints_exist(self):
        """Testa se os endpoints estão definidos"""
        from app.presentation.api.v1.menus import router

        # Verificar se o router tem routes
        assert len(router.routes) > 0

        # Verificar se tem as funções esperadas
        route_names = [getattr(route, "name", "") for route in router.routes]
        assert "get_user_dynamic_menus" in route_names
        assert "get_user_menus_by_context" in route_names
        assert "menu_service_health" in route_names
        assert "debug_menu_structure" in route_names

    def test_menu_router_prefix(self):
        """Testa se o router tem o prefixo correto"""
        from app.presentation.api.v1.menus import router

        assert router.prefix == "/menus"

    def test_menu_router_tags(self):
        """Testa se o router tem as tags corretas"""
        from app.presentation.api.v1.menus import router

        assert "menus" in router.tags

    def test_get_menu_tree_with_none_parent(self, menu_repo):
        """Testa conversão quando há menus com parent_id None"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Root 1",
                "level": 0,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 2,
                "parent_id": None,
                "name": "Root 2",
                "level": 0,
                "sort_order": 2,
                "children": [],
            },
            {
                "id": 3,
                "parent_id": 1,
                "name": "Child",
                "level": 1,
                "sort_order": 1,
                "children": [],
            },
        ]

        result = menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 2
        assert result[0]["name"] == "Root 1"
        assert len(result[0]["children"]) == 1
        assert result[0]["children"][0]["name"] == "Child"

    def test_get_menu_tree_orphaned_children(self, menu_repo):
        """Testa tratamento de filhos órfãos (parent não existe)"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Root",
                "level": 0,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 2,
                "parent_id": 999,
                "name": "Orphan",
                "level": 1,
                "sort_order": 1,
                "children": [],
            },  # Parent não existe
        ]

        result = menu_repo.get_menu_tree(flat_menus)

        # Deve ter apenas o root, órfão deve ser ignorado
        assert len(result) == 1
        assert result[0]["name"] == "Root"
        assert result[0]["children"] == []

    def test_get_menu_tree_deep_hierarchy(self, menu_repo):
        """Testa conversão de hierarquia profunda (3 níveis)"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Level 1",
                "level": 0,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 2,
                "parent_id": 1,
                "name": "Level 2",
                "level": 1,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 3,
                "parent_id": 2,
                "name": "Level 3",
                "level": 2,
                "sort_order": 1,
                "children": [],
            },
        ]

        result = menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 1
        level1 = result[0]
        assert level1["name"] == "Level 1"
        assert len(level1["children"]) == 1

        level2 = level1["children"][0]
        assert level2["name"] == "Level 2"
        assert len(level2["children"]) == 1

        level3 = level2["children"][0]
        assert level3["name"] == "Level 3"
        assert level3["children"] == []

    def test_get_menu_tree_sorting(self, menu_repo):
        """Testa ordenação por sort_order"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Z Menu",
                "level": 0,
                "sort_order": 3,
                "children": [],
            },
            {
                "id": 2,
                "parent_id": None,
                "name": "A Menu",
                "level": 0,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 3,
                "parent_id": None,
                "name": "M Menu",
                "level": 0,
                "sort_order": 2,
                "children": [],
            },
        ]

        result = menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 3
        assert result[0]["name"] == "A Menu"  # sort_order 1
        assert result[1]["name"] == "M Menu"  # sort_order 2
        assert result[2]["name"] == "Z Menu"  # sort_order 3

    def test_get_menu_tree_children_sorting(self, menu_repo):
        """Testa ordenação de filhos"""
        flat_menus = [
            {
                "id": 1,
                "parent_id": None,
                "name": "Parent",
                "level": 0,
                "sort_order": 1,
                "children": [],
            },
            {
                "id": 2,
                "parent_id": 1,
                "name": "Child Z",
                "level": 1,
                "sort_order": 2,
                "children": [],
            },
            {
                "id": 3,
                "parent_id": 1,
                "name": "Child A",
                "level": 1,
                "sort_order": 1,
                "children": [],
            },
        ]

        result = menu_repo.get_menu_tree(flat_menus)

        assert len(result) == 1
        parent = result[0]
        assert len(parent["children"]) == 2
        assert parent["children"][0]["name"] == "Child A"  # sort_order 1
        assert parent["children"][1]["name"] == "Child Z"  # sort_order 2

    @pytest.mark.asyncio
    async def test_get_context_info_system(self, menu_repo):
        """Testa busca de informações de contexto system"""
        result = await menu_repo.get_context_info("system", 1)

        assert result["type"] == "system"
        assert result["id"] == 1
        assert result["name"] == "Sistema Global"

    @pytest.mark.asyncio
    async def test_get_context_info_invalid(self, menu_repo):
        """Testa contexto inválido"""
        result = await menu_repo.get_context_info("invalid", 1)

        assert result["type"] == "invalid"
        assert result["id"] == 1
        assert "fallback" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_get_context_info_company_without_db(self, menu_repo):
        """Testa contexto company sem acesso ao banco"""
        # Como não temos mock do banco, deve retornar fallback
        result = await menu_repo.get_context_info("company", 1)

        assert result["type"] == "company"
        assert result["id"] == 1
        assert "fallback" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_get_context_info_establishment_without_db(self, menu_repo):
        """Testa contexto establishment sem acesso ao banco"""
        result = await menu_repo.get_context_info("establishment", 1)

        assert result["type"] == "establishment"
        assert result["id"] == 1
        assert "fallback" in result["description"].lower()
