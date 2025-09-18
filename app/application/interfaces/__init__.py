"""
Application Interfaces - Contratos e Abstrações
Define contratos que a Application Layer espera da Infrastructure
"""

from .external import CNPJServiceInterface, GeoCodingServiceInterface
from .repositories import CompanyRepositoryInterface, UserRepositoryInterface
from .services import AddressEnrichmentServiceInterface, EmailServiceInterface

__all__ = [
    "CompanyRepositoryInterface",
    "UserRepositoryInterface",
    "AddressEnrichmentServiceInterface",
    "EmailServiceInterface",
    "CNPJServiceInterface",
    "GeoCodingServiceInterface",
]
