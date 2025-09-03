"""
Create Company Use Case - Caso de uso para criação de empresas
Orquestra toda a lógica necessária para criar uma empresa
"""

from structlog import get_logger
from app.application.dto import CreateCompanyCommand
from app.application.interfaces import (
    CompanyRepositoryInterface,
    AddressEnrichmentServiceInterface
)
from app.domain.entities.company import CompanyEntity

logger = get_logger(__name__)


class CreateCompanyUseCase:
    """
    Use Case para criação de empresa
    Responsabilidades:
    1. Validar dados de entrada
    2. Verificar duplicação de CNPJ
    3. Enriquecer endereços (se solicitado)
    4. Persistir empresa
    5. Log de auditoria
    """
    
    def __init__(
        self,
        company_repository: CompanyRepositoryInterface,
        address_enrichment_service: AddressEnrichmentServiceInterface
    ):
        self.company_repository = company_repository
        self.address_enrichment_service = address_enrichment_service
    
    async def execute(self, command: CreateCompanyCommand) -> CompanyEntity:
        """
        Executar criação de empresa
        
        Args:
            command: Dados e configurações para criação
            
        Returns:
            CompanyEntity: Empresa criada com todos os dados
            
        Raises:
            ValueError: CNPJ já existe ou dados inválidos
        """
        logger.info(
            "Iniciando criação de empresa",
            user_id=command.user_id,
            cnpj=command.company_data.people.tax_id,
            enrich_addresses=command.enrich_addresses
        )
        
        # 1. Validar CNPJ único
        await self._validate_unique_cnpj(command.company_data.people.tax_id)
        
        # 2. Enriquecer endereços se solicitado
        if command.enrich_addresses and command.company_data.addresses:
            command.company_data.addresses = await self._enrich_addresses(
                command.company_data.addresses
            )
        
        # 3. Persistir empresa
        company = await self.company_repository.create(command.company_data)
        
        # 4. Log de auditoria
        logger.info(
            "Empresa criada com sucesso",
            company_id=company.id,
            user_id=command.user_id,
            cnpj=command.company_data.people.tax_id,
            addresses_enriched=command.enrich_addresses
        )
        
        return company
    
    async def _validate_unique_cnpj(self, cnpj: str) -> None:
        """Validar se CNPJ é único"""
        exists = await self.company_repository.exists_by_cnpj(cnpj)
        if exists:
            logger.warning("Tentativa de criação com CNPJ duplicado", cnpj=cnpj)
            raise ValueError(f"CNPJ {cnpj} já está cadastrado no sistema")
    
    async def _enrich_addresses(self, addresses: list) -> list:
        """Enriquecer endereços com ViaCEP e geocoding"""
        logger.info("Enriquecendo endereços", count=len(addresses))
        
        # Converter para dict se necessário
        addresses_dict = []
        for addr in addresses:
            if hasattr(addr, 'model_dump'):
                addresses_dict.append(addr.model_dump())
            else:
                addresses_dict.append(dict(addr))
        
        # Enriquecer
        enriched = await self.address_enrichment_service.enrich_multiple_addresses(
            addresses_dict
        )
        
        logger.info("Endereços enriquecidos", count=len(enriched))
        return enriched