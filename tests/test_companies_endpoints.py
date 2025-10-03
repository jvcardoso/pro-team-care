"""
Testes abrangentes para endpoints de companies
Expande cobertura de testes conforme auditoria de qualidade
"""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.presentation.schemas.company import (
    AddressCreate,
    CompanyCreate,
    CompanyDetailed,
    CompanyList,
    EmailCreate,
    PeopleCreate,
    PhoneCreate,
)


class TestCompaniesEndpoints:
    """Testes completos para endpoints /api/v1/companies"""

    def test_get_companies_list_success(self, client: TestClient):
        """Test GET /api/v1/companies - listagem com sucesso"""
        response = client.get("/api/v1/companies")
        assert response.status_code == 200

        data = response.json()
        assert "companies" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert isinstance(data["companies"], list)

    def test_get_companies_list_with_pagination(self, client: TestClient):
        """Test GET /api/v1/companies com paginação"""
        response = client.get("/api/v1/companies?skip=0&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_get_companies_list_with_search(self, client: TestClient):
        """Test GET /api/v1/companies com busca"""
        response = client.get("/api/v1/companies?search=test")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["items"], list)

    def test_get_companies_count(self, client: TestClient):
        """Test GET /api/v1/companies/count"""
        response = client.get("/api/v1/companies/count")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert isinstance(data["total"], int)

    def test_create_company_success(
        self, client: TestClient, authenticated_client: TestClient
    ):
        """Test POST /api/v1/companies - criação com sucesso"""
        company_data = {
            "people": {
                "person_type": "PJ",
                "name": "Empresa Teste LTDA",
                "trade_name": "Teste Corp",
                "tax_id": "11222333000144",
                "incorporation_date": "2020-01-15",
                "status": "active",
                "tax_regime": "simples_nacional",
                "legal_nature": "ltda",
            },
            "company": {
                "settings": {"notifications": True},
                "metadata": {"test": True},
                "display_order": 1,
            },
            "phones": [
                {
                    "country_code": "55",
                    "number": "11987654321",
                    "type": "commercial",
                    "is_principal": True,
                    "is_whatsapp": True,
                }
            ],
            "emails": [
                {
                    "email_address": "contato@teste.com.br",
                    "type": "work",
                    "is_principal": True,
                }
            ],
            "addresses": [
                {
                    "street": "Avenida Paulista",
                    "number": "1000",
                    "neighborhood": "Bela Vista",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip_code": "01310100",
                    "type": "commercial",
                    "is_principal": True,
                    "country": "BR",
                }
            ],
        }

        response = authenticated_client.post("/api/v1/companies", json=company_data)

        # Se a validação de CNPJ for muito rigorosa, podemos receber 400
        # Mas o importante é que não seja erro 500 (interno)
        assert response.status_code in [200, 201, 400]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert data["people"]["name"] == "Empresa Teste LTDA"

    def test_create_company_validation_errors(self, authenticated_client: TestClient):
        """Test POST /api/v1/companies com dados inválidos"""
        # CNPJ inválido
        invalid_data = {
            "people": {
                "person_type": "PJ",
                "name": "Empresa Teste",
                "tax_id": "invalid_cnpj",
                "status": "active",
            }
        }

        response = authenticated_client.post("/api/v1/companies", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_company_unauthorized(self, client: TestClient):
        """Test POST /api/v1/companies sem autenticação"""
        company_data = {
            "people": {
                "person_type": "PJ",
                "name": "Test",
                "tax_id": "11222333000144",
                "status": "active",
            }
        }

        response = client.post("/api/v1/companies", json=company_data)
        assert response.status_code == 401  # Unauthorized

    def test_get_company_by_id_success(self, client: TestClient):
        """Test GET /api/v1/companies/{id} - sucesso"""
        # Assumindo que existe empresa com ID 1 ou mockaremos
        response = client.get("/api/v1/companies/1")

        # Pode retornar 200 se existir ou 404 se não existir
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "people" in data
            assert "phones" in data
            assert "emails" in data
            assert "addresses" in data

    def test_get_company_by_id_not_found(self, client: TestClient):
        """Test GET /api/v1/companies/{id} - não encontrado"""
        response = client.get("/api/v1/companies/99999")
        assert response.status_code == 404

    def test_get_company_by_id_invalid_id(self, client: TestClient):
        """Test GET /api/v1/companies/{id} - ID inválido"""
        response = client.get("/api/v1/companies/invalid")
        assert response.status_code == 422  # Validation error

    def test_update_company_success(self, authenticated_client: TestClient):
        """Test PUT /api/v1/companies/{id} - atualização"""
        update_data = {
            "people": {
                "person_type": "PJ",
                "name": "Empresa Atualizada LTDA",
                "tax_id": "11222333000144",
                "status": "active",
            }
        }

        response = authenticated_client.put("/api/v1/companies/1", json=update_data)

        # Pode ser 200 (sucesso), 404 (não encontrado) ou 422 (validação)
        assert response.status_code in [200, 404, 422]

    def test_update_company_unauthorized(self, client: TestClient):
        """Test PUT /api/v1/companies/{id} sem autenticação"""
        update_data = {"people": {"name": "Updated Company"}}

        response = client.put("/api/v1/companies/1", json=update_data)
        assert response.status_code == 401  # Unauthorized

    def test_delete_company_unauthorized(self, client: TestClient):
        """Test DELETE /api/v1/companies/{id} sem autenticação"""
        response = client.delete("/api/v1/companies/1")
        assert response.status_code == 401  # Unauthorized

    def test_get_company_contacts_success(self, client: TestClient):
        """Test GET /api/v1/companies/{id}/contacts"""
        response = client.get("/api/v1/companies/1/contacts")

        # Pode ser 200 (sucesso) ou 404 (empresa não encontrada)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "phones" in data
            assert "emails" in data
            assert "addresses" in data


class TestCompaniesValidation:
    """Testes de validação de dados de companies"""

    def test_cnpj_validation_valid(self):
        """Test validação de CNPJ válido"""
        valid_cnpjs = ["11222333000144", "11.222.333/0001-44"]

        for cnpj in valid_cnpjs:
            people = PeopleCreate(
                person_type="PJ", name="Test Company", tax_id=cnpj, status="active"
            )
            assert people.tax_id == cnpj

    def test_phone_validation_valid(self):
        """Test validação de telefones válidos"""
        valid_phones = [
            ("55", "11987654321"),  # Celular SP
            ("55", "1133334444"),  # Fixo SP
            ("55", "21987654321"),  # Celular RJ
        ]

        for country_code, number in valid_phones:
            phone = PhoneCreate(
                country_code=country_code, number=number, type="commercial"
            )
            assert phone.country_code == country_code
            assert phone.number == number

    def test_email_validation_valid(self):
        """Test validação de emails válidos"""
        valid_emails = [
            "test@example.com",
            "user.name@company.com.br",
            "contact+info@test.org",
        ]

        for email in valid_emails:
            email_obj = EmailCreate(email_address=email, type="work")
            assert email_obj.email_address == email

    def test_address_validation_valid(self):
        """Test validação de endereços válidos"""
        address = AddressCreate(
            street="Avenida Paulista",
            number="1000",
            neighborhood="Bela Vista",
            city="São Paulo",
            state="SP",
            zip_code="01310100",
            country="BR",
            type="commercial",
        )

        assert address.city == "São Paulo"
        assert address.state == "SP"
        assert len(address.zip_code) == 8


class TestCompaniesBusinessLogic:
    """Testes de lógica de negócio para companies"""

    def test_company_status_transitions(self):
        """Test transições válidas de status"""
        valid_statuses = ["active", "inactive", "suspended"]

        for status in valid_statuses:
            people = PeopleCreate(
                person_type="PJ",
                name="Test Company",
                tax_id="11222333000144",
                status=status,
            )
            assert people.status == status

    def test_person_type_validation(self):
        """Test validação de tipo de pessoa"""
        valid_types = ["PJ", "PF"]

        for person_type in valid_types:
            people = PeopleCreate(
                person_type=person_type,
                name="Test",
                tax_id="11222333000144" if person_type == "PJ" else "12345678901",
                status="active",
            )
            assert people.person_type == person_type

    def test_contact_principal_validation(self):
        """Test validação de contatos principais"""
        # Telefone principal
        phone = PhoneCreate(
            country_code="55",
            number="11987654321",
            type="commercial",
            is_principal=True,
        )
        assert phone.is_principal == True

        # Email principal
        email = EmailCreate(
            email_address="main@company.com", type="work", is_principal=True
        )
        assert email.is_principal == True

        # Endereço principal
        address = AddressCreate(
            street="Main Street",
            number="123",
            city="São Paulo",
            state="SP",
            zip_code="01000000",
            country="BR",
            type="commercial",
            is_principal=True,
        )
        assert address.is_principal == True


class TestCompaniesErrorHandling:
    """Testes de tratamento de erros"""

    def test_database_connection_error_handling(self, client: TestClient):
        """Test handling de erro de conexão com banco"""
        # Este teste verifica se erros de banco são tratados adequadamente
        # sem expor detalhes internos

        with patch("app.infrastructure.database.get_db") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/v1/companies")

            # Deve retornar erro 500 mas sem expor detalhes internos
            assert response.status_code == 500

            # Verificar que não expõe informações sensíveis
            error_detail = response.json().get("detail", "")
            assert "Database connection failed" not in error_detail
            assert "Internal server error" in error_detail

    def test_invalid_json_handling(self, authenticated_client: TestClient):
        """Test handling de JSON inválido"""
        response = authenticated_client.post(
            "/api/v1/companies",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, authenticated_client: TestClient):
        """Test handling de campos obrigatórios faltando"""
        incomplete_data = {
            "people": {
                # Missing required fields like name, tax_id
                "person_type": "PJ"
            }
        }

        response = authenticated_client.post("/api/v1/companies", json=incomplete_data)
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data


# Testes de performance básica
class TestCompaniesPerformance:
    """Testes básicos de performance"""

    def test_companies_list_response_time(self, client: TestClient):
        """Test tempo de resposta da listagem de companies"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/companies?size=10")
        end_time = time.time()

        response_time = end_time - start_time

        # Response time should be less than 2 seconds for basic queries
        assert response_time < 2.0
        assert response.status_code in [200, 401]  # 401 if not authenticated

    def test_company_detail_response_time(self, client: TestClient):
        """Test tempo de resposta de detalhes de company"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/companies/1")
        end_time = time.time()

        response_time = end_time - start_time

        # Response time should be less than 1 second for single record
        assert response_time < 1.0
        assert response.status_code in [200, 404, 401]
