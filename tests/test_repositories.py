import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.auth import get_password_hash
from app.infrastructure.repositories.user_repository import UserRepository


class TestUserRepository:
    """Test suite para o repositório de usuários"""

    @pytest.mark.asyncio
    async def test_create_user(self, async_session: AsyncSession, mock_user_data):
        """Teste de criação de usuário"""
        repository = UserRepository(async_session)

        user_data = mock_user_data.copy()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

        user = await repository.create(user_data)

        assert user.email == mock_user_data["email"]
        assert user.full_name == mock_user_data["full_name"]
        assert user.is_active == True
        assert user.id is not None
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, async_session: AsyncSession, mock_user_data):
        """Teste de busca de usuário por email"""
        repository = UserRepository(async_session)

        # Criar usuário
        user_data = mock_user_data.copy()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        created_user = await repository.create(user_data)

        # Buscar por email
        found_user = await repository.get_by_email(mock_user_data["email"])

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == mock_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, async_session: AsyncSession, mock_user_data):
        """Teste de busca de usuário por ID"""
        repository = UserRepository(async_session)

        # Criar usuário
        user_data = mock_user_data.copy()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        created_user = await repository.create(user_data)

        # Buscar por ID
        found_user = await repository.get_by_id(created_user.id)

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == mock_user_data["email"]

    @pytest.mark.asyncio
    async def test_update_user(self, async_session: AsyncSession, mock_user_data):
        """Teste de atualização de usuário"""
        repository = UserRepository(async_session)

        # Criar usuário
        user_data = mock_user_data.copy()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        created_user = await repository.create(user_data)

        # Atualizar usuário
        update_data = {"full_name": "Updated Name"}
        updated_user = await repository.update(created_user.id, update_data)

        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == mock_user_data["email"]

    @pytest.mark.asyncio
    async def test_delete_user(self, async_session: AsyncSession, mock_user_data):
        """Teste de exclusão de usuário"""
        repository = UserRepository(async_session)

        # Criar usuário
        user_data = mock_user_data.copy()
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        created_user = await repository.create(user_data)

        # Deletar usuário
        result = await repository.delete(created_user.id)
        assert result == True

        # Verificar se foi deletado
        deleted_user = await repository.get_by_id(created_user.id)
        assert deleted_user is None
