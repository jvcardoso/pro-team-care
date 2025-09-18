"""
Company DTOs - Commands e Queries para operações de empresa
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.domain.entities.company import CompanyEntity


@dataclass
class CreateCompanyCommand:
    """Command para criação de empresa - ✅ Usando entidade pura"""

    company_data: CompanyEntity
    user_id: int
    enrich_addresses: bool = True
    send_notification: bool = False


@dataclass
class UpdateCompanyCommand:
    """Command para atualização de empresa - ✅ Usando Dict genérico"""

    company_id: int
    company_data: Dict[str, Any]
    user_id: int
    enrich_addresses: bool = False


@dataclass
class CompanyQueryParams:
    """Parâmetros de busca de empresas"""

    search_term: Optional[str] = None
    status: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    person_type: Optional[str] = None
    page: int = 1
    per_page: int = 20


@dataclass
class EnrichAddressCommand:
    """Command para enriquecimento de endereço"""

    addresses: List[Dict[str, Any]]
    enable_geocoding: bool = True
    enable_viacep: bool = True


@dataclass
class ValidateCNPJCommand:
    """Command para validação de CNPJ"""

    cnpj: str
    check_uniqueness: bool = True
