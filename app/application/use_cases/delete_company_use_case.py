"""
Delete Company Use Case - Caso de uso para exclusão de empresas
"""

from structlog import get_logger
from app.application.interfaces import CompanyRepositoryInterface

logger = get_logger(__name__)


class DeleteCompanyUseCase:
    """
    Use Case para exclusão de empresas
    Responsabilidades:
    1. Excluir empresa por ID
    2. Validar se empresa existe
    3. Log de auditoria de exclusão
    4. Garantir integridade referencial
    """
    
    def __init__(self, company_repository: CompanyRepositoryInterface):
        self.company_repository = company_repository
    
    async def delete_by_id(self, company_id: int, user_id: int) -> bool:
        """
        Excluir empresa por ID
        
        Args:
            company_id: ID da empresa
            user_id: ID do usuário (para auditoria)
            
        Returns:
            True se excluída com sucesso, False caso contrário
        """
        logger.info(
            "Iniciando exclusão de empresa",
            company_id=company_id,
            user_id=user_id
        )
        
        # Verificar se empresa existe
        existing_company = await self.company_repository.get_by_id(company_id)
        if not existing_company:
            logger.warning(
                "Empresa não encontrada para exclusão",
                company_id=company_id,
                user_id=user_id
            )
            return False
        
        logger.info(
            "Empresa encontrada, prosseguindo com exclusão",
            company_id=company_id,
            company_name=existing_company.people.name,
            user_id=user_id
        )
        
        # Excluir empresa
        success = await self.company_repository.delete(company_id)
        
        if success:
            logger.info(
                "Empresa excluída com sucesso",
                company_id=company_id,
                company_name=existing_company.people.name,
                user_id=user_id
            )
        else:
            logger.error(
                "Falha na exclusão da empresa",
                company_id=company_id,
                company_name=existing_company.people.name,
                user_id=user_id
            )
        
        return success