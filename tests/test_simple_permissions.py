"""
Testes Unitários para Sistema de Permissões Simples e Seguro
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.entities.user import User
from app.presentation.decorators.simple_permissions import (
    SimplePermissionChecker,
    check_user_permission_simple,
    permission_checker,
    require_permission,
)


class TestSimplePermissionChecker:
    """Testes para SimplePermissionChecker"""

    @pytest.fixture
    def system_admin_user(self):
        """Usuário system admin para testes"""
        return User(
            id=1,
            person_id=1,
            company_id=1,
            email_address="admin@system.com",
            password="",
            is_active=True,
            is_system_admin=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def normal_user(self):
        """Usuário normal para testes"""
        return User(
            id=15,
            person_id=65,
            company_id=65,
            email_address="teste_02@teste.com",
            password="",
            is_active=True,
            is_system_admin=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_system_admin_bypass(self, system_admin_user):
        """Teste: System admin tem acesso irrestrito"""
        checker = SimplePermissionChecker()

        result = await checker.check_permission(
            user_id=system_admin_user.id,
            permission="companies.view",
            context_type="system",
            is_system_admin=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_normal_user_with_permission(self, normal_user):
        """Teste: Usuário normal com permissão tem acesso"""
        checker = SimplePermissionChecker()

        # Mock da query do banco que retorna permissão encontrada
        with patch("app.infrastructure.database.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalar.return_value = True
            mock_db.execute.return_value = mock_result

            result = await checker.check_permission(
                user_id=normal_user.id,
                permission="companies.view",
                context_type="system",
                is_system_admin=False,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_normal_user_without_permission(self, normal_user):
        """Teste: Usuário normal sem permissão é negado"""
        checker = SimplePermissionChecker()

        # Mock da query do banco que retorna permissão não encontrada
        with patch("app.infrastructure.database.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalar.return_value = False
            mock_db.execute.return_value = mock_result

            result = await checker.check_permission(
                user_id=normal_user.id,
                permission="companies.create",
                context_type="system",
                is_system_admin=False,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_database_error_denies_access(self, normal_user):
        """Teste: Erro no banco nega acesso por segurança"""
        checker = SimplePermissionChecker()

        # Mock da query do banco que gera erro
        with patch("app.infrastructure.database.async_session") as mock_session:
            mock_session.side_effect = Exception("Database error")

            result = await checker.check_permission(
                user_id=normal_user.id,
                permission="companies.view",
                context_type="system",
                is_system_admin=False,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_permission_with_context_id(self, normal_user):
        """Teste: Verificação de permissão com context_id específico"""
        checker = SimplePermissionChecker()

        # Mock da query do banco
        with patch("app.infrastructure.database.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalar.return_value = True
            mock_db.execute.return_value = mock_result

            result = await checker.check_permission(
                user_id=normal_user.id,
                permission="users.view",
                context_type="company",
                context_id=65,
                is_system_admin=False,
            )

            assert result is True

            # Verificar se a query incluiu o context_id
            call_args = mock_db.execute.call_args
            query_params = call_args[0][1]
            assert query_params["context_id"] == 65


class TestPermissionDecorator:
    """Testes para decorator require_permission"""

    @pytest.fixture
    def mock_current_user(self):
        """Mock de usuário atual"""
        return User(
            id=15,
            person_id=65,
            company_id=65,
            email_address="teste_02@teste.com",
            password="",
            is_active=True,
            is_system_admin=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_decorator_allows_access_with_permission(self, mock_current_user):
        """Teste: Decorator permite acesso com permissão válida"""

        # Mock da verificação de permissão
        with patch.object(permission_checker, "check_permission", return_value=True):

            @require_permission("companies.view", context_type="system")
            async def test_endpoint(current_user: User):
                return {"message": "success"}

            # Executar função decorada
            result = await test_endpoint(current_user=mock_current_user)

            assert result == {"message": "success"}

    @pytest.mark.asyncio
    async def test_decorator_denies_access_without_permission(self, mock_current_user):
        """Teste: Decorator nega acesso sem permissão válida"""
        from fastapi import HTTPException

        # Mock da verificação de permissão
        with patch.object(permission_checker, "check_permission", return_value=False):

            @require_permission("companies.create", context_type="system")
            async def test_endpoint(current_user: User):
                return {"message": "success"}

            # Deve gerar HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(current_user=mock_current_user)

            assert exc_info.value.status_code == 403
            assert "permission_denied" in str(exc_info.value.detail)


class TestContextFilters:
    """Testes para filtros de contexto"""

    @pytest.fixture
    def system_admin_user(self):
        return User(
            id=1,
            person_id=1,
            company_id=1,
            email_address="admin@system.com",
            password="",
            is_active=True,
            is_system_admin=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.fixture
    def normal_user(self):
        return User(
            id=15,
            person_id=65,
            company_id=65,
            email_address="teste_02@teste.com",
            password="",
            is_active=True,
            is_system_admin=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_company_filter_system_admin(self, system_admin_user):
        """Teste: System admin não tem filtros aplicados"""
        from sqlalchemy import select

        from app.infrastructure.filters.context_filters import ContextFilter
        from app.infrastructure.orm.models import Company

        query = select(Company)
        filtered_query = await ContextFilter.apply_company_filter(
            query, system_admin_user
        )

        # Query deve permanecer inalterada para system admin
        assert filtered_query == query

    @pytest.mark.asyncio
    async def test_company_filter_normal_user(self, normal_user):
        """Teste: Usuário normal tem filtros aplicados"""
        from sqlalchemy import select

        from app.infrastructure.filters.context_filters import ContextFilter
        from app.infrastructure.orm.models import Company

        query = select(Company)
        filtered_query = await ContextFilter.apply_company_filter(query, normal_user)

        # Query deve ter filtro aplicado
        assert filtered_query != query
        # Verificar se o filtro foi aplicado corretamente
        query_str = str(filtered_query)
        assert "companies.id = :id_1" in query_str or "companies.id = ?" in query_str


class TestUtilityFunctions:
    """Testes para funções utilitárias"""

    @pytest.mark.asyncio
    async def test_check_user_permission_simple(self):
        """Teste: Função utilitária de verificação manual"""

        with patch.object(permission_checker, "check_permission", return_value=True):
            result = await check_user_permission_simple(
                user_id=15, permission="companies.view", context_type="system"
            )

            assert result is True


class TestRealWorldScenarios:
    """Testes de cenários do mundo real"""

    @pytest.mark.asyncio
    async def test_scenario_teste_02_user_companies_access(self):
        """Teste: Cenário real do usuário teste_02@teste.com"""

        # Simular usuário teste_02
        user = User(
            id=15,
            person_id=65,
            company_id=65,
            email_address="teste_02@teste.com",
            password="",
            is_active=True,
            is_system_admin=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock da query que retorna permissão encontrada (como no banco real)
        with patch("app.infrastructure.database.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_result = AsyncMock()
            mock_result.scalar.return_value = True  # Usuário tem companies.view
            mock_db.execute.return_value = mock_result

            result = await permission_checker.check_permission(
                user_id=user.id,
                permission="companies.view",
                context_type="system",
                is_system_admin=False,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_scenario_isolation_between_companies(self):
        """Teste: Isolamento entre empresas diferentes"""

        # Usuário da empresa 65
        user_company_65 = User(
            id=15,
            company_id=65,
            is_system_admin=False,
            email_address="user@company65.com",
            password="",
            person_id=1,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Usuário da empresa 66
        user_company_66 = User(
            id=16,
            company_id=66,
            is_system_admin=False,
            email_address="user@company66.com",
            password="",
            person_id=2,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        from sqlalchemy import select

        from app.infrastructure.filters.context_filters import ContextFilter
        from app.infrastructure.orm.models import Company

        # Ambos devem ter filtros diferentes aplicados
        query = select(Company)

        filtered_65 = await ContextFilter.apply_company_filter(query, user_company_65)
        filtered_66 = await ContextFilter.apply_company_filter(query, user_company_66)

        # As queries filtradas devem ser diferentes
        assert str(filtered_65) != str(filtered_66)


# Configuração para pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
