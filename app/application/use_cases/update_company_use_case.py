"""
Update Company Use Case - Caso de uso para atualização de empresas
"""

from typing import Optional

from structlog import get_logger

from app.application.dto import UpdateCompanyCommand
from app.application.interfaces import CompanyRepositoryInterface
from app.domain.entities.company import CompanyEntity

logger = get_logger(__name__)


class UpdateCompanyUseCase:
    """
    Use Case para atualização de empresas
    Responsabilidades:
    1. Atualizar dados da empresa por ID
    2. Validar se empresa existe
    3. Log de auditoria de alterações
    4. Retornar dados atualizados
    """

    def __init__(self, company_repository: CompanyRepositoryInterface):
        self.company_repository = company_repository

    async def update_by_id(
        self, command: UpdateCompanyCommand
    ) -> Optional[CompanyEntity]:
        """
        Atualizar empresa por ID

        Args:
            command: Command contendo dados da empresa e metadados

        Returns:
            CompanyEntity ou None se não encontrada
        """
        logger.info(
            "Iniciando atualização de empresa",
            company_id=command.company_id,
            user_id=command.user_id,
            enrich_addresses=command.enrich_addresses,
            has_people_data=bool(command.company_data.people),
            has_company_data=bool(command.company_data.company),
            phones_count=(
                len(command.company_data.phones) if command.company_data.phones else 0
            ),
            emails_count=(
                len(command.company_data.emails) if command.company_data.emails else 0
            ),
            addresses_count=(
                len(command.company_data.addresses)
                if command.company_data.addresses
                else 0
            ),
        )

        # Verificar se empresa existe
        existing_company = await self.company_repository.get_by_id(command.company_id)
        if not existing_company:
            logger.warning(
                "Empresa não encontrada para atualização",
                company_id=command.company_id,
                user_id=command.user_id,
            )
            return None

        logger.info(
            "Empresa encontrada, prosseguindo com atualização",
            company_id=command.company_id,
            company_name=existing_company.people.name,
            user_id=command.user_id,
        )

        # Atualizar empresa
        updated_company = await self.company_repository.update(
            command.company_id, command.company_data
        )

        if updated_company:
            logger.info(
                "Empresa atualizada com sucesso",
                company_id=command.company_id,
                company_name=updated_company.people.name,
                user_id=command.user_id,
            )
        else:
            logger.error(
                "Falha na atualização da empresa",
                company_id=command.company_id,
                user_id=command.user_id,
            )

        return updated_company
