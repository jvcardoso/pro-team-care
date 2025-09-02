"""
Get Company Use Case - Caso de uso para busca de empresas
"""

from typing import Optional, List
from structlog import get_logger
from app.application.dto import CompanyQueryParams
from app.application.interfaces import CompanyRepositoryInterface
from app.domain.entities.company import CompanyEntity

logger = get_logger(__name__)


class GetCompanyUseCase:
    """
    Use Case para busca de empresas
    Responsabilidades:
    1. Buscar empresa por ID
    2. Buscar empresa por CNPJ
    3. Buscar empresas com filtros
    4. Log de auditoria de acesso
    """
    
    def __init__(self, company_repository: CompanyRepositoryInterface):
        self.company_repository = company_repository
    
    async def get_by_id(self, company_id: int, user_id: int) -> Optional[CompanyEntity]:
        """
        Buscar empresa por ID
        
        Args:
            company_id: ID da empresa
            user_id: ID do usuário (para auditoria)
            
        Returns:
            CompanyEntity ou None se não encontrada
        """
        logger.info(
            "Buscando empresa por ID",
            company_id=company_id,
            user_id=user_id
        )
        
        company = await self.company_repository.get_by_id(company_id)
        
        if company:
            logger.info(
                "Empresa encontrada",
                company_id=company_id,
                company_name=company.people.name,
                user_id=user_id
            )
        else:
            logger.warning(
                "Empresa não encontrada",
                company_id=company_id,
                user_id=user_id
            )
        
        return company
    
    async def get_by_cnpj(self, cnpj: str, user_id: int) -> Optional[CompanyEntity]:
        """
        Buscar empresa por CNPJ
        
        Args:
            cnpj: CNPJ da empresa
            user_id: ID do usuário (para auditoria)
            
        Returns:
            CompanyEntity ou None se não encontrada
        """
        logger.info(
            "Buscando empresa por CNPJ",
            cnpj=cnpj,
            user_id=user_id
        )
        
        company = await self.company_repository.get_by_cnpj(cnpj)
        
        if company:
            logger.info(
                "Empresa encontrada por CNPJ",
                company_id=company.id,
                cnpj=cnpj,
                company_name=company.people.name,
                user_id=user_id
            )
        else:
            logger.warning(
                "Empresa não encontrada por CNPJ",
                cnpj=cnpj,
                user_id=user_id
            )
        
        return company
    
    async def search(self, params: CompanyQueryParams, user_id: int) -> List[CompanyEntity]:
        """
        Buscar empresas com filtros
        
        Args:
            params: Parâmetros de busca
            user_id: ID do usuário (para auditoria)
            
        Returns:
            Lista de empresas encontradas
        """
        logger.info(
            "Buscando empresas com filtros",
            search_term=params.search_term,
            status=params.status,
            city=params.city,
            state=params.state,
            user_id=user_id
        )
        
        # Converter dataclass para dict
        filters = {
            'search_term': params.search_term,
            'status': params.status,
            'city': params.city,
            'state': params.state,
            'person_type': params.person_type,
            'page': params.page,
            'per_page': params.per_page
        }
        
        # Remover filtros None
        filters = {k: v for k, v in filters.items() if v is not None}
        
        companies = await self.company_repository.search(filters)
        
        logger.info(
            "Busca de empresas concluída",
            total_found=len(companies),
            filters=filters,
            user_id=user_id
        )
        
        return companies