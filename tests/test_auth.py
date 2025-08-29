import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.user_repository import UserRepository
from app.application.use_cases.auth_use_case import AuthUseCase
from app.infrastructure.auth import get_password_hash


class TestAuth:
    """Test suite para autenticação"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: TestClient, async_session: AsyncSession, mock_user_data):
        """Teste de registro de usuário com sucesso"""
        response = client.post("/api/v1/auth/register", json=mock_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user_data["email"]
        assert data["full_name"] == mock_user_data["full_name"]
        assert data["is_active"] == True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Senha não deve ser retornada
    
    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, client: TestClient, async_session: AsyncSession, mock_user_data):
        """Teste de registro de usuário duplicado"""
        # Primeiro registro
        response1 = client.post("/api/v1/auth/register", json=mock_user_data)
        assert response1.status_code == 200
        
        # Segundo registro com mesmo email
        response2 = client.post("/api/v1/auth/register", json=mock_user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: TestClient, async_session: AsyncSession, mock_user_data):
        """Teste de login com sucesso"""
        # Registrar usuário primeiro
        client.post("/api/v1/auth/register", json=mock_user_data)
        
        # Tentar login
        login_data = {
            "username": mock_user_data["email"],
            "password": mock_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: TestClient):
        """Teste de login com credenciais inválidas"""
        login_data = {
            "username": "invalid@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: TestClient, async_session: AsyncSession, mock_user_data):
        """Teste de obtenção do usuário atual"""
        # Registrar e fazer login
        client.post("/api/v1/auth/register", json=mock_user_data)
        
        login_data = {
            "username": mock_user_data["email"],
            "password": mock_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Usar token para acessar endpoint protegido
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user_data["email"]
        assert data["full_name"] == mock_user_data["full_name"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_no_token(self, client: TestClient):
        """Teste de acesso a endpoint protegido sem token"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]