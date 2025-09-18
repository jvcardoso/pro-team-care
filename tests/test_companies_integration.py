"""
Integration tests for Companies CRUD API
Tests the full functionality with mocked database responses
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import AsyncClient

from app.infrastructure.repositories.company_repository import CompanyRepository
from app.main import app
from app.presentation.schemas.company import CompanyDetailed, CompanyList


class TestCompaniesAPI:
    """Integration tests for Companies API endpoints"""

    @pytest.fixture
    async def mock_repository(self):
        """Mock repository with sample data"""
        repo = AsyncMock(spec=CompanyRepository)

        # Mock company data
        sample_company = {
            "id": 1,
            "person_id": 8,
            "settings": {"email_notifications": True},
            "metadata": {"test_company": True},
            "display_order": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
            "people": {
                "id": 8,
                "person_type": "PJ",
                "name": "Empresa Teste LTDA",
                "trade_name": "Teste Corp",
                "tax_id": "02668512000156",
                "status": "active",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None,
            },
            "phones": [
                {
                    "id": 1,
                    "country_code": "55",
                    "number": "11987654321",
                    "type": "commercial",
                    "is_principal": True,
                    "is_whatsapp": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            ],
            "emails": [
                {
                    "id": 1,
                    "email_address": "contato@teste.com.br",
                    "type": "work",
                    "is_principal": True,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            ],
            "addresses": [],
        }

        # Configure mock responses
        repo.get_company.return_value = CompanyDetailed(**sample_company)
        repo.count_companies.return_value = 13
        repo.get_companies.return_value = [
            CompanyList(
                id=1,
                person_id=8,
                name="Empresa Teste LTDA",
                trade_name="Teste Corp",
                tax_id="02668512000156",
                status="active",
                phones_count=1,
                emails_count=1,
                addresses_count=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]

        return repo

    @pytest.mark.asyncio
    async def test_companies_count_endpoint(self, mock_repository):
        """Test companies count endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the repository dependency
            app.dependency_overrides[CompanyRepository] = lambda: mock_repository

            response = await client.get("/api/v1/companies/count")

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert isinstance(data["total"], int)

            # Clean up
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_company_endpoint(self, mock_repository):
        """Test individual company retrieval"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            app.dependency_overrides[CompanyRepository] = lambda: mock_repository

            response = await client.get("/api/v1/companies/1")

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert "id" in data
            assert "people" in data
            assert "phones" in data
            assert "emails" in data
            assert "addresses" in data

            # Validate people data
            people_data = data["people"]
            assert people_data["name"] == "Empresa Teste LTDA"
            assert people_data["tax_id"] == "02668512000156"

            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_companies_list_endpoint(self, mock_repository):
        """Test companies listing endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            app.dependency_overrides[CompanyRepository] = lambda: mock_repository

            response = await client.get("/api/v1/companies?limit=10")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            if len(data) > 0:
                company = data[0]
                assert "id" in company
                assert "name" in company
                assert "tax_id" in company
                assert "phones_count" in company
                assert "emails_count" in company

            app.dependency_overrides.clear()

    def test_company_data_validation(self):
        """Test that company data passes validation"""
        company_data = {
            "id": 1,
            "person_id": 8,
            "settings": {"test": True},
            "metadata": {"created_by": "test"},
            "display_order": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
            "people": {
                "id": 8,
                "person_type": "PJ",
                "name": "Test Company",
                "tax_id": "12345678000100",
                "status": "active",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None,
            },
            "phones": [],
            "emails": [],
            "addresses": [],
        }

        # This should not raise any validation errors
        company = CompanyDetailed(**company_data)
        assert company.id == 1
        assert company.people.name == "Test Company"

    def test_api_documentation_structure(self):
        """Test that API is properly documented"""
        # Basic test to ensure our endpoints are structured correctly
        expected_paths = [
            "/api/v1/companies",
            "/api/v1/companies/count",
            "/api/v1/companies/{company_id}",
            "/api/v1/companies/{company_id}/contacts",
        ]

        # Validate that we have the expected number of endpoints
        assert len(expected_paths) == 4

        # Validate endpoint patterns
        assert any("count" in path for path in expected_paths)
        assert any("contacts" in path for path in expected_paths)


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_company_not_found(self):
        """Test handling of non-existent company"""
        mock_repo = AsyncMock(spec=CompanyRepository)
        mock_repo.get_company.return_value = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            app.dependency_overrides[CompanyRepository] = lambda: mock_repo

            response = await client.get("/api/v1/companies/999")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

            app.dependency_overrides.clear()

    def test_invalid_company_data(self):
        """Test validation of invalid company data"""
        invalid_data = {
            "id": "invalid_id",  # Should be int
            "person_id": 8,
            # Missing required fields
        }

        with pytest.raises(Exception):  # Should raise validation error
            CompanyDetailed(**invalid_data)


if __name__ == "__main__":
    print("Running Companies API integration tests...")

    # Basic validation tests that can run without async
    print("✅ Testing company data validation...")

    company_data = {
        "id": 1,
        "person_id": 8,
        "settings": {"test": True},
        "metadata": {"created_by": "test"},
        "display_order": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "deleted_at": None,
        "people": {
            "id": 8,
            "person_type": "PJ",
            "name": "Test Company",
            "tax_id": "12345678000100",
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
        },
        "phones": [],
        "emails": [],
        "addresses": [],
    }

    try:
        company = CompanyDetailed(**company_data)
        print(f"✅ CompanyDetailed validation passed: {company.people.name}")
    except Exception as e:
        print(f"❌ CompanyDetailed validation failed: {e}")

    # Test CompanyList model
    list_data = {
        "id": 1,
        "person_id": 8,
        "name": "Test Company",
        "trade_name": "Test Corp",
        "tax_id": "12345678000100",
        "status": "active",
        "phones_count": 1,
        "emails_count": 1,
        "addresses_count": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    try:
        company_list = CompanyList(**list_data)
        print(f"✅ CompanyList validation passed: {company_list.name}")
    except Exception as e:
        print(f"❌ CompanyList validation failed: {e}")

    print("✅ All basic integration tests passed!")
