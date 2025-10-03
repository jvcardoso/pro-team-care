#!/usr/bin/env python3
"""
Testes de integração para cenários completos Home Care
Cenários baseados no documento de análise
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.contract_repository import ContractRepository
from app.infrastructure.repositories.medical_authorization_repository import MedicalAuthorizationRepository
from app.presentation.schemas.contract import ContractCreate
from app.presentation.schemas.medical_authorization import MedicalAuthorizationCreate


class TestHomeCareIntegration:
    """Testes de integração para cenários completos Home Care"""

    @pytest_asyncio.fixture
    async def contract_repo(self, db_session: AsyncSession):
        """Fixture para repositório de contratos"""
        return ContractRepository(db_session)

    @pytest_asyncio.fixture
    async def auth_repo(self, db_session: AsyncSession):
        """Fixture para repositório de autorizações médicas"""
        return MedicalAuthorizationRepository(db_session)

    @pytest.mark.asyncio
    async def test_scenario_unimed_corporate_contract(self, contract_repo, auth_repo):
        """Teste: Cenário UNIMED - Contrato corporativo com 10 vidas e rotatividade"""

        # === FASE 1: Criar contrato corporativo ===
        contract_data = ContractCreate(
            client_id=65,  # UNIMED
            contract_number="UNIMED-2025-001",
            contract_type="CORPORATIVO",
            lives_contracted=10,
            lives_minimum=8,  # Tolerância ±2
            lives_maximum=12,
            allows_substitution=True,
            control_period="MONTHLY",
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

        contract = await contract_repo.create(contract_data)

        # Validações do contrato
        assert contract.contract_type == "CORPORATIVO"
        assert contract.lives_contracted == 10
        assert contract.lives_minimum == 8
        assert contract.lives_maximum == 12
        assert contract.allows_substitution is True

        # === FASE 2: Adicionar vidas iniciais ===
        # Simular adição de 10 funcionários
        lives_added = 0
        for i in range(1, 11):
            person_id = 200 + i  # IDs fictícios de pessoas
            await contract_repo.add_contract_life(
                contract_id=contract.id,
                person_id=person_id,
                start_date=date(2025, 1, 1),
                relationship_type="FUNCIONARIO"
            )
            lives_added += 1

        # Verificar que todas as vidas foram adicionadas
        active_lives = await contract_repo.get_active_lives_count(contract.id)
        assert active_lives == 10

        # === FASE 3: Criar autorizações médicas ===
        # Autorização para Maria (funcionária 1) - Diabética
        maria_auth = MedicalAuthorizationCreate(
            contract_id=contract.id,
            person_id=201,  # Maria
            service_id=1,  # Aplicação de medicação EV
            authorization_code="AUTH-MARIA-001",
            medical_indication="Diabetes tipo 2 - insulina NPH e regular",
            special_instructions="Aplicar insulina NPH pela manhã, regular antes das refeições",
            priority_level="HIGH",
            sessions_authorized=30,  # 30 aplicações por mês
            monthly_limit=30,
            daily_limit=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            authorized_by=10  # Médico responsável
        )

        maria_authorization = await auth_repo.create(maria_auth)

        # Validações da autorização
        assert maria_authorization.authorization_code == "AUTH-MARIA-001"
        assert maria_authorization.sessions_authorized == 30
        assert maria_authorization.priority_level == "HIGH"
        assert maria_authorization.is_active is True

        # === FASE 4: Simular uso de serviços ===
        # Maria usa 5 aplicações na primeira semana
        await auth_repo.update_sessions_used(maria_authorization.id, 5)
        updated_auth = await auth_repo.get_by_id(maria_authorization.id)

        assert updated_auth.sessions_used == 5
        assert updated_auth.sessions_remaining == 25

        # === FASE 5: Testar substituição de vida ===
        # Ana (funcionária 2) sai da empresa
        await contract_repo.remove_contract_life(
            contract_id=contract.id,
            person_id=202,  # Ana
            end_date=date(2025, 1, 15),
            reason="Desligamento da empresa"
        )

        # Verificar que uma vida foi removida
        active_lives_after_removal = await contract_repo.get_active_lives_count(contract.id)
        assert active_lives_after_removal == 9

        # Adicionar Pedro como substituto
        await contract_repo.add_contract_life(
            contract_id=contract.id,
            person_id=211,  # Pedro (novo funcionário)
            start_date=date(2025, 1, 16),
            relationship_type="FUNCIONARIO"
        )

        # Verificar que voltou a 10 vidas
        final_lives = await contract_repo.get_active_lives_count(contract.id)
        assert final_lives == 10

        # === FASE 6: Verificar histórico completo ===
        history = await contract_repo.get_lives_history(contract.id)
        assert len(history) >= 3  # Adições + remoção + substituição

        # Verificar que o contrato ainda está dentro dos limites
        assert 8 <= final_lives <= 12  # Dentro da tolerância

    @pytest.mark.asyncio
    async def test_scenario_individual_person_contract(self, contract_repo, auth_repo):
        """Teste: Cenário pessoa física individual (João + família)"""

        # === FASE 1: Criar contrato individual ===
        contract_data = ContractCreate(
            client_id=2,  # João Silva (pessoa física)
            contract_number="PF-JOAO-2025-001",
            contract_type="INDIVIDUAL",
            lives_contracted=3,  # João + esposa + 2 filhos
            allows_substitution=False,  # Família fixa
            control_period="MONTHLY",
            plan_name="Plano Familiar Básico",
            monthly_value=Decimal("2500.00"),
            start_date=date(2025, 1, 1)
        )

        contract = await contract_repo.create(contract_data)

        # Validações específicas para contrato individual
        assert contract.contract_type == "INDIVIDUAL"
        assert contract.lives_contracted == 3
        assert contract.allows_substitution is False
        assert contract.lives_minimum is None  # Sem tolerância para individual

        # === FASE 2: Adicionar membros da família ===
        family_members = [
            (201, "João Silva", "TITULAR"),
            (202, "Maria Silva", "DEPENDENTE"),  # Esposa
            (203, "Pedro Silva", "DEPENDENTE"),   # Filho
            (204, "Ana Silva", "DEPENDENTE")      # Filha
        ]

        for person_id, name, relationship in family_members:
            await contract_repo.add_contract_life(
                contract_id=contract.id,
                person_id=person_id,
                start_date=date(2025, 1, 1),
                relationship_type=relationship
            )

        active_lives = await contract_repo.get_active_lives_count(contract.id)
        assert active_lives == 4  # João + 3 dependentes

        # === FASE 3: Criar autorizações específicas ===
        # João - Hipertenso
        joao_auth = MedicalAuthorizationCreate(
            contract_id=contract.id,
            person_id=201,  # João
            service_id=3,  # Aferição de pressão arterial
            authorization_code="AUTH-JOAO-001",
            medical_indication="Hipertensão leve - monitoramento mensal",
            sessions_authorized=12,  # 1 por mês
            monthly_limit=1,
            daily_limit=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            authorized_by=10
        )

        # Maria - Pós-cirúrgica
        maria_auth = MedicalAuthorizationCreate(
            contract_id=contract.id,
            person_id=202,  # Maria
            service_id=4,  # Fisioterapia
            authorization_code="AUTH-MARIA-001",
            medical_indication="Pós-cirurgia de joelho - reabilitação",
            sessions_authorized=20,  # 20 sessões
            monthly_limit=4,  # 4 por mês
            daily_limit=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            authorized_by=10
        )

        joao_authorization = await auth_repo.create(joao_auth)
        maria_authorization = await auth_repo.create(maria_auth)

        # === FASE 4: Testar validações de limites ===
        # João tenta usar 2 aferições no mesmo dia (limite diário = 1)
        with pytest.raises(ValueError, match="Daily limit exceeded"):
            await auth_repo.validate_session_usage(joao_authorization.id, sessions_to_use=2)

        # João usa 1 aferição (dentro do limite)
        await auth_repo.validate_session_usage(joao_authorization.id, sessions_to_use=1)
        await auth_repo.update_sessions_used(joao_authorization.id, 1)

        # Verificar uso
        updated_joao_auth = await auth_repo.get_by_id(joao_authorization.id)
        assert updated_joao_auth.sessions_used == 1
        assert updated_joao_auth.sessions_remaining == 11

    @pytest.mark.asyncio
    async def test_scenario_business_person_clinic(self, contract_repo, auth_repo):
        """Teste: Cenário empresário/clínica (Dr. Carlos)"""

        # === FASE 1: Criar contrato empresarial ===
        contract_data = ContractCreate(
            client_id=3,  # Dr. Carlos/Clínica
            contract_number="EMP-CARLOS-2025-001",
            contract_type="EMPRESARIAL",
            lives_contracted=5,  # Equipe clínica
            allows_substitution=False,  # Equipe estável
            control_period="MONTHLY",
            plan_name="Plano Empresarial Saúde",
            monthly_value=Decimal("7500.00"),
            start_date=date(2025, 1, 1)
        )

        contract = await contract_repo.create(contract_data)

        assert contract.contract_type == "EMPRESARIAL"
        assert contract.lives_contracted == 5

        # === FASE 2: Adicionar equipe clínica ===
        clinical_staff = [
            (301, "Dr. Carlos", "TITULAR"),
            (302, "Enf. Ana", "FUNCIONARIO"),
            (303, "Enf. Pedro", "FUNCIONARIO"),
            (304, "Tec. Maria", "FUNCIONARIO"),
            (305, "Aux. João", "FUNCIONARIO")
        ]

        for person_id, name, relationship in clinical_staff:
            await contract_repo.add_contract_life(
                contract_id=contract.id,
                person_id=person_id,
                start_date=date(2025, 1, 1),
                relationship_type=relationship
            )

        active_lives = await contract_repo.get_active_lives_count(contract.id)
        assert active_lives == 5

        # === FASE 3: Autorizações médicas para equipe ===
        # Dr. Carlos - Consultas médicas
        carlos_auth = MedicalAuthorizationCreate(
            contract_id=contract.id,
            person_id=301,  # Dr. Carlos
            service_id=5,  # Consulta médica domiciliar
            authorization_code="AUTH-CARLOS-001",
            medical_indication="Médico responsável pela clínica",
            sessions_authorized=50,  # Capacidade de 50 consultas/mês
            monthly_limit=50,
            daily_limit=5,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            authorized_by=301  # Auto-autorização
        )

        carlos_authorization = await auth_repo.create(carlos_auth)

        # === FASE 4: Simular atividade da clínica ===
        # Dr. Carlos realiza 10 consultas na primeira semana
        await auth_repo.update_sessions_used(carlos_authorization.id, 10)

        updated_auth = await auth_repo.get_by_id(carlos_authorization.id)
        assert updated_auth.sessions_used == 10
        assert updated_auth.sessions_remaining == 40

    @pytest.mark.asyncio
    async def test_limits_validation_integration(self, contract_repo, auth_repo):
        """Teste: Validação integrada de limites entre contrato e autorizações"""

        # === FASE 1: Criar contrato com limites ===
        contract_data = ContractCreate(
            client_id=65,
            contract_number="LIMITS-TEST-001",
            contract_type="CORPORATIVO",
            lives_contracted=5,
            lives_minimum=4,
            lives_maximum=6,
            allows_substitution=True,
            control_period="MONTHLY",
            plan_name="Teste de Limites",
            monthly_value=Decimal("5000.00"),
            start_date=date(2025, 1, 1)
        )

        contract = await contract_repo.create(contract_data)

        # === FASE 2: Adicionar vidas ===
        for i in range(1, 6):
            await contract_repo.add_contract_life(
                contract_id=contract.id,
                person_id=400 + i,
                start_date=date(2025, 1, 1),
                relationship_type="FUNCIONARIO"
            )

        # === FASE 3: Criar autorizações com limites ===
        for i in range(1, 6):
            auth_data = MedicalAuthorizationCreate(
                contract_id=contract.id,
                person_id=400 + i,
                service_id=1,  # Mesmo serviço para todos
                authorization_code=f"AUTH-LIMITS-{i}",
                medical_indication=f"Funcionário {i} - Teste de limites",
                sessions_authorized=10,
                monthly_limit=10,
                daily_limit=2,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                authorized_by=10
            )
            await auth_repo.create(auth_data)

        # === FASE 4: Testar validações de limites ===
        # Buscar uma autorização
        authorizations = await auth_repo.list_by_contract(contract.id)
        first_auth = authorizations[0]

        # Usar sessões dentro do limite
        await auth_repo.validate_session_usage(first_auth.id, sessions_to_use=2)
        await auth_repo.update_sessions_used(first_auth.id, 2)

        # Tentar usar mais que o limite diário
        with pytest.raises(ValueError, match="Daily limit exceeded"):
            await auth_repo.validate_session_usage(first_auth.id, sessions_to_use=1)  # Já usou 2, limite é 2

        # === FASE 5: Testar limites de contrato ===
        # Remover uma vida (ficar com 4)
        await contract_repo.remove_contract_life(
            contract_id=contract.id,
            person_id=405,
            end_date=date(2025, 1, 15),
            reason="Teste de limites"
        )

        active_lives = await contract_repo.get_active_lives_count(contract.id)
        assert active_lives == 4  # Dentro do limite mínimo (4)

        # Tentar ficar com menos que o mínimo
        with pytest.raises(ValueError, match="Below minimum lives"):
            await contract_repo.remove_contract_life(
                contract_id=contract.id,
                person_id=404,
                end_date=date(2025, 1, 16),
                reason="Teste abaixo do mínimo"
            )

    @pytest.mark.asyncio
    async def test_audit_trail_integration(self, contract_repo, auth_repo):
        """Teste: Rastreabilidade completa de auditoria"""

        # === FASE 1: Criar contrato ===
        contract_data = ContractCreate(
            client_id=65,
            contract_number="AUDIT-TEST-001",
            contract_type="CORPORATIVO",
            lives_contracted=3,
            allows_substitution=True,
            plan_name="Teste de Auditoria",
            monthly_value=Decimal("3000.00"),
            start_date=date(2025, 1, 1)
        )

        contract = await contract_repo.create(contract_data)

        # === FASE 2: Adicionar vidas ===
        for i in range(1, 4):
            await contract_repo.add_contract_life(
                contract_id=contract.id,
                person_id=500 + i,
                start_date=date(2025, 1, 1),
                relationship_type="FUNCIONARIO"
            )

        # === FASE 3: Operações que geram auditoria ===
        # Remover uma vida
        await contract_repo.remove_contract_life(
            contract_id=contract.id,
            person_id=502,
            end_date=date(2025, 1, 10),
            reason="Auditoria: Remoção teste"
        )

        # Adicionar nova vida
        await contract_repo.add_contract_life(
            contract_id=contract.id,
            person_id=504,
            start_date=date(2025, 1, 11),
            relationship_type="FUNCIONARIO"
        )

        # === FASE 4: Criar e usar autorização ===
        auth_data = MedicalAuthorizationCreate(
            contract_id=contract.id,
            person_id=501,
            service_id=1,
            authorization_code="AUTH-AUDIT-001",
            medical_indication="Auditoria: Teste de uso",
            sessions_authorized=5,
            monthly_limit=5,
            daily_limit=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            authorized_by=10
        )

        authorization = await auth_repo.create(auth_data)
        await auth_repo.update_sessions_used(authorization.id, 3)

        # === FASE 5: Verificar auditoria completa ===
        # Histórico de vidas do contrato
        lives_history = await contract_repo.get_lives_history(contract.id)
        assert len(lives_history) >= 2  # Adição + remoção

        # Histórico da autorização
        auth_history = await auth_repo.get_history(authorization.id)
        assert len(auth_history) >= 2  # Criação + uso de sessões

        # Verificar que todos os registros têm campos de auditoria
        for record in lives_history + auth_history:
            assert hasattr(record, 'created_at')
            assert hasattr(record, 'created_by')
            assert record.created_at is not None