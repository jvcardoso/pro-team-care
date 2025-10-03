#!/usr/bin/env python3
"""
Testes específicos para CRUD de contratos Home Care
"""

import pytest
import pytest_asyncio
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# Import models from ORM
from app.infrastructure.orm.models import Contract, ContractLive, ServicesCatalog, ContractService

# Import repository
from app.infrastructure.repositories.contract_repository import ContractRepository

# Import schemas
from app.presentation.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractLiveCreate,
    ContractLiveUpdate
)


class TestContractsCRUD:
    """Testes CRUD completos para contratos Home Care"""

    @pytest_asyncio.fixture
    async def contract_repo(self, async_session: AsyncSession):
        """Fixture para repositório de contratos"""
        return ContractRepository(async_session)



    @pytest.mark.asyncio
    async def test_create_contract_success(self, contract_repo, async_session):
        """Teste: Criar contrato com sucesso"""
        # First create a client in the database
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,  # Will be set after creating person
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company",
            tax_id="12345678000190",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST001",
            type="matriz",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        # Create contract data
        contract_data = ContractCreate(
            client_id=client.id,
            contract_number="UNIMED-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            lives_minimum=8,
            lives_maximum=12,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Home Care Corporativo UNIMED",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1),
            service_addresses=[{
                "street": "Rua da Saúde",
                "number": "100",
                "neighborhood": "Centro",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01234-567"
            }]
        )

        # Act
        contract_dict = contract_data.model_dump()
        contract = await contract_repo.create_contract(contract_dict)

        # Assert
        assert contract.id is not None
        assert contract.contract_number.startswith("CLI")
        assert contract.contract_type == "CORPORATIVO"
        assert contract.lives_contracted == 10
        assert contract.lives_minimum == 8
        assert contract.lives_maximum == 12
        assert contract.allows_substitution is True
        assert contract.control_period == "MONTHLY"
        assert contract.monthly_value == Decimal("15000.00")
        assert contract.status == "active"

    @pytest.mark.asyncio
    async def test_create_contract_individual_person(self, contract_repo, async_session):
        """Teste: Criar contrato para pessoa física"""
        # Arrange - Create test data
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PF",
            name="João Silva",
            tax_id="12345678901",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST002",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        contract_data = ContractCreate(
            client_id=client.id,  # Use the created client ID
            contract_number="PF-2025-001",
            contract_type="INDIVIDUAL",
            lives_contracted=3,  # Titular + 2 dependentes
            allows_substitution=False,
            payment_frequency="MONTHLY",
            plan_name="Plano Familiar Básico",
            monthly_value=Decimal("2500.00"),
            start_date=date(2025, 1, 1)
        )

        # Act
        contract_dict = contract_data.model_dump()
        contract = await contract_repo.create_contract(contract_dict)

        # Assert
        assert contract.contract_type == "INDIVIDUAL"
        assert contract.lives_contracted == 3
        assert contract.allows_substitution is False
        assert contract.lives_minimum is None  # Para individual, sem tolerância

    @pytest.mark.asyncio
    async def test_create_contract_business_person(self, contract_repo, async_session):
        """Teste: Criar contrato para empresário"""
        # Arrange - Create test data
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Clínica Saúde Ltda",
            tax_id="98765432000190",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST003",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        contract_data = ContractCreate(
            client_id=client.id,  # Use the created client ID
            contract_number="EMP-2025-001",
            contract_type="EMPRESARIAL",
            lives_contracted=5,  # Equipe clínica
            allows_substitution=False,
            payment_frequency="MONTHLY",
            plan_name="Plano Empresarial Saúde",
            monthly_value=Decimal("7500.00"),
            start_date=date(2025, 1, 1)
        )

        # Act
        contract_dict = contract_data.model_dump()
        contract = await contract_repo.create_contract(contract_dict)

        # Assert
        assert contract.contract_type == "EMPRESARIAL"
        assert contract.lives_contracted == 5
        assert contract.allows_substitution is False

    @pytest.mark.asyncio
    async def test_get_contract_by_id(self, contract_repo, async_session):
        """Teste: Buscar contrato por ID"""
        # Arrange - Create test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company Get",
            tax_id="11111111000111",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST004",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        sample_contract_data = ContractCreate(
            client_id=client.id,
            contract_number="GET-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Test Get",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1)
        )

        created_contract = await contract_repo.create_contract(sample_contract_data.model_dump())

        # Act
        contract = await contract_repo.get_contract_by_id(created_contract.id)

        # Assert
        assert contract is not None
        assert contract.id == created_contract.id
        assert contract.contract_number == created_contract.contract_number

    @pytest.mark.asyncio
    async def test_update_contract(self, contract_repo, async_session):
        """Teste: Atualizar contrato"""
        # Arrange - Create test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company Update",
            tax_id="22222222000122",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST005",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        sample_contract_data = ContractCreate(
            client_id=client.id,
            contract_number="UPD-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Original",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1)
        )

        created_contract = await contract_repo.create_contract(sample_contract_data.model_dump())

        update_data = ContractUpdate(
            plan_name="Plano Home Care Corporativo UNIMED - Atualizado",
            monthly_value=Decimal("16000.00"),
            lives_contracted=12
        )

        # Act
        update_dict = update_data.model_dump()
        updated_contract = await contract_repo.update_contract(created_contract.id, update_dict)

        # Assert
        assert updated_contract.plan_name == "Plano Home Care Corporativo UNIMED - Atualizado"
        assert updated_contract.monthly_value == Decimal("16000.00")
        assert updated_contract.lives_contracted == 12

    @pytest.mark.asyncio
    async def test_list_contracts_with_filters(self, contract_repo, async_session):
        """Teste: Listar contratos com filtros"""
        # Arrange - Create test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company List",
            tax_id="33333333000133",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST006",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        sample_contract_data = ContractCreate(
            client_id=client.id,
            contract_number="LIST-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Test List",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1)
        )

        await contract_repo.create_contract(sample_contract_data.model_dump())

        # Act - Filtrar por tipo
        contracts_result = await contract_repo.list_contracts(contract_type="CORPORATIVO")
        contracts = contracts_result["contracts"]

        # Assert
        assert len(contracts) > 0
        assert all(c.contract_type == "CORPORATIVO" for c in contracts)

    @pytest.mark.asyncio
    async def test_contract_validation_rules(self, contract_repo, async_session):
        """Teste: Validações de regras de negócio"""
        # Arrange - Create valid test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company Validation",
            tax_id="44444444000144",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST007",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        # Arrange - Dados inválidos
        invalid_data = ContractCreate(
            client_id=client.id,
            contract_number="TEST-001",
            contract_type="INVALID_TYPE",  # Tipo inválido
            lives_contracted=10,
            payment_frequency="MONTHLY",
            plan_name="Test Contract",
            monthly_value=Decimal("1000.00"),
            start_date=date(2025, 1, 1)
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await contract_repo.create_contract(invalid_data.model_dump())

    @pytest.mark.asyncio
    async def test_contract_status_transitions(self, contract_repo, async_session):
        """Teste: Transições de status do contrato"""
        # Arrange - Create test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company Status",
            tax_id="55555555000155",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST008",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        sample_contract_data = ContractCreate(
            client_id=client.id,
            contract_number="STATUS-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Test Status",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1)
        )

        created_contract = await contract_repo.create_contract(sample_contract_data.model_dump())

        # Act - Suspender contrato
        await contract_repo.update_contract_status(created_contract.id, "SUSPENDED")
        suspended_contract = await contract_repo.get_contract_by_id(created_contract.id)

        # Assert
        assert suspended_contract.status == "SUSPENDED"

        # Act - Reativar contrato
        await contract_repo.update_contract_status(created_contract.id, "ACTIVE")
        active_contract = await contract_repo.get_contract_by_id(created_contract.id)

        # Assert
        assert active_contract.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_contract_audit_trail(self, contract_repo, async_session):
        """Teste: Rastreabilidade de auditoria"""
        # Arrange - Create test data first
        from app.infrastructure.orm.models import Client, People, Company, Establishments

        # Create a company first
        company = Company(
            person_id=None,
            settings={},
            metadata_={}
        )
        async_session.add(company)
        await async_session.flush()

        # Create a person associated with the company
        person = People(
            company_id=company.id,
            person_type="PJ",
            name="Test Company Audit",
            tax_id="66666666000166",
            status="active"
        )
        async_session.add(person)
        await async_session.flush()

        # Update company to reference the person
        company.person_id = person.id
        await async_session.flush()

        # Create an establishment for the client
        establishment = Establishments(
            person_id=person.id,
            company_id=company.id,
            code="EST009",
            type="clinica",
            category="clinica",
            is_active=True,
            is_principal=True,
            display_order=1
        )
        async_session.add(establishment)
        await async_session.flush()

        # Create a client
        client = Client(
            person_id=person.id,
            establishment_id=establishment.id
        )
        async_session.add(client)
        await async_session.flush()

        sample_contract_data = ContractCreate(
            client_id=client.id,
            contract_number="AUDIT-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            allows_substitution=True,
            payment_frequency="MONTHLY",
            plan_name="Plano Test Audit",
            monthly_value=Decimal("15000.00"),
            start_date=date(2025, 1, 1)
        )

        created_contract = await contract_repo.create_contract(sample_contract_data.model_dump())

        # Act
        contract = await contract_repo.get_contract_by_id(created_contract.id)

        # Assert
        assert contract.created_at is not None
        assert contract.updated_at is not None
        # Verificar se campos de auditoria estão presentes
        assert hasattr(contract, 'created_by') or hasattr(contract, 'updated_by')