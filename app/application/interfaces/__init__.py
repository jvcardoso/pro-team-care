"""
Application Interfaces - Contratos e Abstrações
Define contratos que a Application Layer espera da Infrastructure
"""

from .repositories import CompanyRepositoryInterface, UserRepositoryInterface
from .services import AddressEnrichmentServiceInterface, EmailServiceInterface
from .external import CNPJServiceInterface, GeoCodingServiceInterface

__all__ = [
    "CompanyRepositoryInterface",
    "UserRepositoryInterface", 
    "AddressEnrichmentServiceInterface",
    "EmailServiceInterface",
    "CNPJServiceInterface",
    "GeoCodingServiceInterface"
]