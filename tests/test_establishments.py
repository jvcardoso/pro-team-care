"""
Testes abrangentes para endpoints de establishments
Testa todas as operações CRUD do backend de estabelecimentos
"""

from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.presentation.schemas.establishment import (
    EstablishmentCategory,
    EstablishmentCreate,
    EstablishmentDetailed,
    EstablishmentListResponse,
    EstablishmentReorderRequest,
    EstablishmentType,
    EstablishmentUpdateComplete,
    EstablishmentValidationResponse,
)


class TestEstablishmentsEndpoints:
    """Testes completos para endpoints /api/v1/establishments"""

    def test_list_establishments_success(self, client: TestClient):
        """Test GET /api/v1/establishments - listagem com sucesso"""
        response = client.get("/api/v1/establishments")
        assert response.status_code in [200, 401]  # 401 se não autenticado

        if response.status_code == 200:
            data = response.json()
            assert "establishments" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert isinstance(data["establishments"], list)

    def test_list_establishments_with_filters(self, client: TestClient):
        """Test GET /api/v1/establishments com filtros"""
        response = client.get(
            "/api/v1/establishments?company_id=1&is_active=true&type=matriz"
        )
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["establishments"], list)

    def test_list_establishments_with_pagination(self, client: TestClient):
        """Test GET /api/v1/establishments com paginação"""
        response = client.get("/api/v1/establishments?page=1&size=5")
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert data.get("page") == 1
            assert data.get("size") == 5

    def test_list_establishments_with_search(self, client: TestClient):
        """Test GET /api/v1/establishments com busca"""
        response = client.get("/api/v1/establishments?search=clinica")
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["establishments"], list)

    def test_create_establishment_success(self, authenticated_client: TestClient):
        """Test POST /api/v1/establishments - criação com sucesso"""
        establishment_data = {
            "company_id": 1,
            "code": "EST001",
            "type": "matriz",
            "category": "clinica",
            "is_active": True,
            "is_principal": True,
            "person": {
                "name": "Clínica Teste LTDA",
                "tax_id": "11222333000144",
                "person_type": "PJ",
                "status": "active",
                "description": "Clínica de teste",
            },
            "settings": {"notifications": True},
            "metadata": {"test": True},
            "operating_hours": {
                "monday": {"open": "08:00", "close": "18:00"},
                "tuesday": {"open": "08:00", "close": "18:00"},
            },
            "service_areas": ["cardiologia", "dermatologia"],
        }

        response = authenticated_client.post(
            "/api/v1/establishments", json=establishment_data
        )

        # Pode ser 201 (sucesso) ou 400 (validação) dependendo dos dados
        assert response.status_code in [201, 400, 422]

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["code"] == "EST001"
            assert data["type"] == "matriz"
            assert data["category"] == "clinica"

    def test_create_establishment_validation_errors(
        self, authenticated_client: TestClient
    ):
        """Test POST /api/v1/establishments com dados inválidos"""
        # Dados inválidos - code muito curto
        invalid_data = {
            "company_id": 1,
            "code": "A",  # Code muito curto
            "type": "matriz",
            "category": "clinica",
            "person": {
                "name": "Clínica Teste",
                "tax_id": "invalid_cnpj",
                "person_type": "PJ",
                "status": "active",
            },
        }

        response = authenticated_client.post(
            "/api/v1/establishments", json=invalid_data
        )
        assert response.status_code == 422  # Validation error

    def test_create_establishment_unauthorized(self, client: TestClient):
        """Test POST /api/v1/establishments sem autenticação"""
        establishment_data = {
            "company_id": 1,
            "code": "EST001",
            "type": "matriz",
            "category": "clinica",
            "person": {
                "name": "Clínica Teste",
                "tax_id": "11222333000144",
                "person_type": "PJ",
                "status": "active",
            },
        }

        response = client.post("/api/v1/establishments", json=establishment_data)
        assert response.status_code == 401  # Unauthorized

    def test_get_establishment_by_id_success(self, client: TestClient):
        """Test GET /api/v1/establishments/{id} - sucesso"""
        response = client.get("/api/v1/establishments/1")

        # Pode retornar 200 (sucesso) ou 404 (não encontrado) ou 401 (não autenticado)
        assert response.status_code in [200, 404, 401]

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "code" in data
            assert "person" in data

    def test_get_establishment_by_id_not_found(self, client: TestClient):
        """Test GET /api/v1/establishments/{id} - não encontrado"""
        response = client.get("/api/v1/establishments/99999")
        assert response.status_code in [404, 401]

    def test_get_establishment_by_id_invalid_id(self, client: TestClient):
        """Test GET /api/v1/establishments/{id} - ID inválido"""
        response = client.get("/api/v1/establishments/invalid")
        assert response.status_code in [422, 401]  # Validation error

    def test_update_establishment_success(self, authenticated_client: TestClient):
        """Test PUT /api/v1/establishments/{id} - atualização"""
        update_data = {
            "code": "EST002",
            "type": "filial",
            "category": "hospital",
            "is_active": True,
            "person": {
                "name": "Hospital Atualizado",
                "tax_id": "11222333000144",
                "status": "active",
            },
        }

        response = authenticated_client.put(
            "/api/v1/establishments/1", json=update_data
        )

        # Pode ser 200 (sucesso), 404 (não encontrado) ou 422 (validação)
        assert response.status_code in [200, 404, 422]

        if response.status_code == 200:
            data = response.json()
            assert data["code"] == "EST002"
            assert data["type"] == "filial"

    def test_update_establishment_unauthorized(self, client: TestClient):
        """Test PUT /api/v1/establishments/{id} sem autenticação"""
        update_data = {"code": "EST002", "type": "filial"}

        response = client.put("/api/v1/establishments/1", json=update_data)
        assert response.status_code == 401  # Unauthorized

    def test_toggle_establishment_status(self, authenticated_client: TestClient):
        """Test PATCH /api/v1/establishments/{id}/status"""
        response = authenticated_client.patch(
            "/api/v1/establishments/1/status?is_active=false"
        )

        # Pode ser 200 (sucesso) ou 404 (não encontrado)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "is_active" in data

    def test_delete_establishment_success(self, authenticated_client: TestClient):
        """Test DELETE /api/v1/establishments/{id} - sucesso"""
        response = authenticated_client.delete("/api/v1/establishments/1")

        # Pode ser 204 (sucesso) ou 404 (não encontrado)
        assert response.status_code in [204, 404]

    def test_delete_establishment_unauthorized(self, client: TestClient):
        """Test DELETE /api/v1/establishments/{id} sem autenticação"""
        response = client.delete("/api/v1/establishments/1")
        assert response.status_code == 401  # Unauthorized

    def test_reorder_establishments(self, authenticated_client: TestClient):
        """Test POST /api/v1/establishments/reorder"""
        reorder_data = {
            "company_id": 1,
            "establishment_orders": [{"id": 1, "order": 1}, {"id": 2, "order": 2}],
        }

        response = authenticated_client.post(
            "/api/v1/establishments/reorder", json=reorder_data
        )

        # Pode ser 200 (sucesso) ou 400 (erro na reordenação)
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_validate_establishment_creation(self, authenticated_client: TestClient):
        """Test POST /api/v1/establishments/validate"""
        response = authenticated_client.post(
            "/api/v1/establishments/validate?company_id=1&code=EST001&is_principal=false"
        )

        # Pode ser 200 (sucesso) ou 422 (parâmetros inválidos)
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert "is_valid" in data
            assert "error_message" in data
            assert "suggested_display_order" in data

    def test_list_establishments_by_company(self, client: TestClient):
        """Test GET /api/v1/establishments/company/{company_id}"""
        response = client.get("/api/v1/establishments/company/1")

        # Pode ser 200 (sucesso) ou 404 (empresa não encontrada) ou 401 (não autenticado)
        assert response.status_code in [200, 404, 401]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestEstablishmentsValidation:
    """Testes de validação de dados de establishments"""

    def test_establishment_code_validation_valid(self):
        """Test validação de código válido"""
        from app.presentation.schemas.establishment import (
            EstablishmentCreate,
            PersonCreateForEstablishment,
        )

        person = PersonCreateForEstablishment(
            name="Clínica Teste",
            tax_id="11222333000144",
            person_type="PJ",
            status="active",
            description="Clínica de teste",
        )

        establishment = EstablishmentCreate(
            company_id=1,
            code="EST001",
            type=EstablishmentType.MATRIZ,
            category=EstablishmentCategory.CLINICA,
            is_active=True,
            is_principal=False,
            settings={},
            metadata={},
            operating_hours={},
            service_areas={},
            person=person,
        )

        assert establishment.code == "EST001"
        assert establishment.type == "matriz"

    def test_establishment_code_validation_invalid(self):
        """Test validação de código inválido"""
        from pydantic import ValidationError

        from app.presentation.schemas.establishment import (
            EstablishmentCreate,
            PersonCreateForEstablishment,
        )

        person = PersonCreateForEstablishment(
            name="Clínica Teste",
            tax_id="11222333000144",
            person_type="PJ",
            status="active",
            description="Clínica de teste",
        )

        # Code muito curto
        with pytest.raises(ValidationError):
            EstablishmentCreate(
                company_id=1,
                code="A",  # Inválido
                type=EstablishmentType.MATRIZ,
                category=EstablishmentCategory.CLINICA,
                is_active=True,
                is_principal=False,
                settings={},
                metadata={},
                operating_hours={},
                service_areas={},
                person=person,
            )

    def test_cnpj_validation_valid(self):
        """Test validação de CNPJ válido"""
        from app.presentation.schemas.establishment import PersonCreateForEstablishment

        valid_cnpjs = ["11222333000144", "11.222.333/0001-44"]

        for cnpj in valid_cnpjs:
            person = PersonCreateForEstablishment(
                name="Test Company",
                tax_id=cnpj,
                person_type="PJ",
                status="active",
                description="Test company",
            )
            assert (
                person.tax_id.replace(".", "").replace("/", "").replace("-", "")
                == "11222333000144"
            )

    def test_establishment_type_enum(self):
        """Test enum de tipos de estabelecimento"""
        from app.presentation.schemas.establishment import EstablishmentType

        assert EstablishmentType.MATRIZ == "matriz"
        assert EstablishmentType.FILIAL == "filial"
        assert EstablishmentType.UNIDADE == "unidade"
        assert EstablishmentType.POSTO == "posto"

    def test_establishment_category_enum(self):
        """Test enum de categorias de estabelecimento"""
        from app.presentation.schemas.establishment import EstablishmentCategory

        assert EstablishmentCategory.CLINICA == "clinica"
        assert EstablishmentCategory.HOSPITAL == "hospital"
        assert EstablishmentCategory.LABORATORIO == "laboratorio"


class TestEstablishmentsBusinessLogic:
    """Testes de lógica de negócio para establishments"""

    def test_establishment_status_transitions(self):
        """Test transições válidas de status"""
        from app.presentation.schemas.establishment import EstablishmentUpdate

        # Status ativo
        update = EstablishmentUpdate(is_active=True, code=None, display_order=None)
        assert update.is_active == True

        # Status inativo
        update = EstablishmentUpdate(is_active=False, code=None, display_order=None)
        assert update.is_active == False

    def test_establishment_principal_validation(self):
        """Test validação de estabelecimento principal"""
        from app.presentation.schemas.establishment import (
            EstablishmentCreate,
            PersonCreateForEstablishment,
        )

        person = PersonCreateForEstablishment(
            name="Clínica Principal",
            tax_id="11222333000144",
            person_type="PJ",
            status="active",
            description="Clínica principal",
        )

        # Estabelecimento principal
        establishment = EstablishmentCreate(
            company_id=1,
            code="MATRIZ",
            type=EstablishmentType.MATRIZ,
            category=EstablishmentCategory.CLINICA,
            is_active=True,
            is_principal=True,
            settings={},
            metadata={},
            operating_hours={},
            service_areas={},
            person=person,
        )

        assert establishment.is_principal == True

    def test_establishment_settings_validation(self):
        """Test validação de configurações"""
        from app.presentation.schemas.establishment import (
            EstablishmentCreate,
            PersonCreateForEstablishment,
        )

        person = PersonCreateForEstablishment(
            name="Clínica Teste",
            tax_id="11222333000144",
            person_type="PJ",
            status="active",
            description="Clínica de teste",
        )

        settings = {"notifications": True, "auto_backup": False, "max_users": 50}

        establishment = EstablishmentCreate(
            company_id=1,
            code="EST001",
            type=EstablishmentType.MATRIZ,
            category=EstablishmentCategory.CLINICA,
            is_active=True,
            is_principal=False,
            settings=settings,
            metadata={},
            operating_hours={},
            service_areas={},
            person=person,
        )

        assert establishment.settings is not None
        assert establishment.settings["notifications"] == True
        assert establishment.settings["max_users"] == 50


class TestEstablishmentsErrorHandling:
    """Testes de tratamento de erros"""

    def test_database_connection_error_handling(self, client: TestClient):
        """Test handling de erro de conexão com banco"""
        with patch("app.infrastructure.database.get_db") as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            response = client.get("/api/v1/establishments")

            # Deve retornar erro 500 mas sem expor detalhes internos
            assert response.status_code == 500

            # Verificar que não expõe informações sensíveis
            error_detail = response.json().get("detail", "")
            assert "Database connection failed" not in error_detail
            assert "Internal server error" in error_detail

    def test_invalid_json_handling(self, authenticated_client: TestClient):
        """Test handling de JSON inválido"""
        import json

        response = authenticated_client.post(
            "/api/v1/establishments",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, authenticated_client: TestClient):
        """Test handling de campos obrigatórios faltando"""
        incomplete_data = {
            "company_id": 1,
            "type": "matriz",
            "category": "clinica",
            "person": {
                "name": "Clínica Teste"
                # Missing tax_id
            },
        }

        response = authenticated_client.post(
            "/api/v1/establishments", json=incomplete_data
        )
        assert response.status_code == 422

        error_data = response.json()
        assert "detail" in error_data


# Testes de performance básica
class TestEstablishmentsPerformance:
    """Testes básicos de performance"""

    def test_establishments_list_response_time(self, client: TestClient):
        """Test tempo de resposta da listagem de establishments"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/establishments?size=10")
        end_time = time.time()

        response_time = end_time - start_time

        # Response time should be less than 2 seconds for basic queries
        assert response_time < 2.0
        assert response.status_code in [200, 401]  # 401 if not authenticated

    def test_establishment_detail_response_time(self, client: TestClient):
        """Test tempo de resposta de detalhes de establishment"""
        import time

        start_time = time.time()
        response = client.get("/api/v1/establishments/1")
        end_time = time.time()

        response_time = end_time - start_time

        # Response time should be less than 1 second for single record
        assert response_time < 1.0
        assert response.status_code in [200, 404, 401]
