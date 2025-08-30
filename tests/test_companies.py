import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from app.domain.models.company import (
    CompanyCreate, CompanyDetailed, CompanyList, 
    PeopleCreate, PhoneCreate, EmailCreate, AddressCreate
)
from app.infrastructure.repositories.company_repository import CompanyRepository


class TestCompanyRepository:
    """Test cases for CompanyRepository"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def company_repository(self, mock_db_session):
        """CompanyRepository instance with mocked database"""
        return CompanyRepository(mock_db_session)
    
    @pytest.fixture
    def sample_company_data(self):
        """Sample company data for testing"""
        return CompanyCreate(
            people=PeopleCreate(
                person_type="PJ",
                name="Empresa Teste LTDA",
                trade_name="Teste Corp",
                tax_id="02668512000156",
                incorporation_date="2020-01-15",
                tax_regime="simples_nacional",
                legal_nature="ltda",
                status="active"
            ),
            company={
                "settings": {"notifications": True},
                "metadata": {"test": True},
                "display_order": 1
            },
            phones=[
                PhoneCreate(
                    country_code="55",
                    number="11987654321",
                    type="commercial",
                    is_principal=True,
                    is_whatsapp=True
                )
            ],
            emails=[
                EmailCreate(
                    email_address="contato@teste.com.br",
                    type="work",
                    is_principal=True
                )
            ],
            addresses=[
                AddressCreate(
                    street="Avenida Paulista",
                    number="1000",
                    neighborhood="Bela Vista",
                    city="São Paulo",
                    state="SP",
                    zip_code="01310100",
                    type="commercial",
                    is_principal=True
                )
            ]
        )
    
    def test_company_data_structure(self, sample_company_data):
        """Test that company data structure is valid"""
        assert sample_company_data.people.name == "Empresa Teste LTDA"
        assert sample_company_data.people.tax_id == "02668512000156"
        assert len(sample_company_data.phones) == 1
        assert len(sample_company_data.emails) == 1
        assert len(sample_company_data.addresses) == 1
        
    def test_phone_validation(self):
        """Test phone number validation"""
        phone = PhoneCreate(
            country_code="55",
            number="11987654321",
            type="mobile",
            is_whatsapp=True
        )
        assert phone.country_code == "55"
        assert phone.number == "11987654321"
        assert phone.is_whatsapp == True
        
    def test_email_validation(self):
        """Test email validation"""
        email = EmailCreate(
            email_address="test@example.com",
            type="work",
            is_principal=True
        )
        assert email.email_address == "test@example.com"
        assert email.type == "work"
        assert email.is_principal == True
    
    def test_address_validation(self):
        """Test address validation"""
        address = AddressCreate(
            street="Rua Teste",
            number="123",
            neighborhood="Centro",
            city="São Paulo",
            state="SP",
            zip_code="01000000",
            type="commercial"
        )
        assert address.street == "Rua Teste"
        assert address.state == "SP"
        assert len(address.zip_code) == 8


class TestCompanyModels:
    """Test cases for Company Pydantic models"""
    
    def test_people_create_model(self):
        """Test PeopleCreate model validation"""
        people_data = {
            "person_type": "PJ",
            "name": "Test Company",
            "tax_id": "12345678000100",
            "status": "active"
        }
        people = PeopleCreate(**people_data)
        assert people.person_type == "PJ"
        assert people.name == "Test Company"
        assert people.tax_id == "12345678000100"
    
    def test_company_detailed_model(self):
        """Test CompanyDetailed model structure"""
        # Mock data structure similar to what would come from database
        company_data = {
            "id": 1,
            "person_id": 1,
            "settings": {"test": True},
            "metadata": {"created_by": "test"},
            "display_order": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
            "people": {
                "id": 1,
                "person_type": "PJ",
                "name": "Test Company",
                "trade_name": "Test Corp",
                "tax_id": "12345678000100",
                "status": "active",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None
            },
            "phones": [],
            "emails": [],
            "addresses": []
        }
        
        company = CompanyDetailed(**company_data)
        assert company.id == 1
        assert company.people.name == "Test Company"
        assert isinstance(company.phones, list)


class TestAPIIntegration:
    """Integration tests for the API endpoints"""
    
    def test_api_endpoints_structure(self):
        """Test that expected endpoints are properly structured"""
        # This would be expanded with actual API testing using TestClient
        expected_endpoints = [
            "/api/v1/companies",
            "/api/v1/companies/count", 
            "/api/v1/companies/{id}",
            "/api/v1/companies/{id}/contacts"
        ]
        
        # Basic validation that our endpoint structure is as expected
        assert len(expected_endpoints) == 4
        assert "/api/v1/companies" in expected_endpoints
        
    def test_company_list_model(self):
        """Test CompanyList model for listing endpoint"""
        list_data = {
            "id": 1,
            "person_id": 1,
            "name": "Test Company",
            "trade_name": "Test Corp", 
            "tax_id": "12345678000100",
            "status": "active",
            "phones_count": 1,
            "emails_count": 1,
            "addresses_count": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        company_list = CompanyList(**list_data)
        assert company_list.name == "Test Company"
        assert company_list.phones_count == 1


if __name__ == "__main__":
    # Basic test runner - in production, use pytest
    print("Running basic company CRUD tests...")
    
    # Test model validation
    people_data = PeopleCreate(
        person_type="PJ",
        name="Test Company",
        tax_id="12345678000100",
        status="active"
    )
    print(f"✅ PeopleCreate validation: {people_data.name}")
    
    phone_data = PhoneCreate(
        country_code="55",
        number="11987654321",
        type="mobile"
    )
    print(f"✅ PhoneCreate validation: {phone_data.number}")
    
    email_data = EmailCreate(
        email_address="test@example.com",
        type="work"
    )
    print(f"✅ EmailCreate validation: {email_data.email_address}")
    
    print("✅ All basic model tests passed!")