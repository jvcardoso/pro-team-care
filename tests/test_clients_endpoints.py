"""
Testes para endpoints de clientes
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.orm.models import Client, Companies, Establishments, People
from app.presentation.schemas.client import ClientStatus, PersonType


class TestClientsEndpoints:
    """Testes para endpoints de clientes"""

    @pytest.mark.asyncio
    async def test_get_client_by_id_success(self, authenticated_client: TestClient, async_session: AsyncSession):
        """Testa obter cliente por ID com sucesso"""
        # Criar dados de teste
        company = Companies(
            name="Empresa Teste",
            tax_id="12345678000123",
            email="teste@empresa.com"
        )
        async_session.add(company)
        await async_session.flush()

        establishment = Establishments(
            name="Estabelecimento Teste",
            code="EST001",
            company_id=company.id,
            address="Rua Teste, 123"
        )
        async_session.add(establishment)
        await async_session.flush()

        person = People(
            name="João Silva",
            tax_id="12345678901",
            person_type=PersonType.PF,
            birth_date="1990-01-01"
        )
        async_session.add(person)
        await async_session.flush()

        client = Client(
            person_id=person.id,
            establishment_id=establishment.id,
            status=ClientStatus.ACTIVE,
            client_code="CLI001"
        )
        async_session.add(client)
        await async_session.flush()
        await async_session.commit()

        # Fazer requisição
        response = authenticated_client.get(f"/api/v1/clients/{client.id}")

        # Verificar resposta
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura básica
        assert "id" in data
        assert "name" in data
        assert "tax_id" in data
        assert "status" in data
        assert "person_type" in data
        assert "establishment_name" in data
        assert "company_name" in data

        # Verificar dados específicos
        assert data["id"] == client.id
        assert data["name"] == person.name
        assert data["tax_id"] == person.tax_id
        assert data["status"] == ClientStatus.ACTIVE
        assert data["person_type"] == PersonType.PF
        assert data["client_code"] == "CLI001"

    def test_get_client_by_id_not_found(self, authenticated_client: TestClient):
        """Testa obter cliente inexistente"""
        response = authenticated_client.get("/api/v1/clients/99999")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "não encontrado" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_clients(self, authenticated_client: TestClient, async_session: AsyncSession):
        """Testa listar clientes"""
        # Criar dados de teste
        company = Companies(
            name="Empresa Teste",
            tax_id="12345678000123",
            email="teste@empresa.com"
        )
        async_session.add(company)
        await async_session.flush()

        establishment = Establishments(
            name="Estabelecimento Teste",
            code="EST001",
            company_id=company.id,
            address="Rua Teste, 123"
        )
        async_session.add(establishment)
        await async_session.flush()

        person = People(
            name="João Silva",
            tax_id="12345678901",
            person_type=PersonType.PF
        )
        async_session.add(person)
        await async_session.flush()

        client = Client(
            person_id=person.id,
            establishment_id=establishment.id,
            status=ClientStatus.ACTIVE,
            client_code="CLI001"
        )
        async_session.add(client)
        await async_session.flush()
        await async_session.commit()

        # Fazer requisição
        response = authenticated_client.get("/api/v1/clients/")

        # Verificar resposta
        assert response.status_code == 200
        data = response.json()

        # Verificar estrutura
        assert "clients" in data
        assert "total" in data
        assert isinstance(data["clients"], list)
        assert len(data["clients"]) >= 1

        # Verificar primeiro cliente
        first_client = data["clients"][0]
        assert "id" in first_client
        assert "name" in first_client
        assert "tax_id" in first_client
        assert "status" in first_client</content>
</xai:function_call: write>
<parameter name="filePath">tests/test_clients_endpoints.py
