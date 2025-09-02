"""
Domain Entities - Clean Architecture
Entidades puras de domínio sem dependências de frameworks
"""

from .user import User
from .company import (
    PersonType,
    PersonStatus,
    PhoneType,
    LineType,
    EmailType,
    AddressType,
    AccessDifficulty,
    PhoneEntity,
    EmailEntity,
    AddressEntity,
    PeopleEntity,
    CompanyEntity
)

__all__ = [
    "User",
    "PersonType",
    "PersonStatus", 
    "PhoneType",
    "LineType",
    "EmailType",
    "AddressType",
    "AccessDifficulty",
    "PhoneEntity",
    "EmailEntity",
    "AddressEntity",
    "PeopleEntity",
    "CompanyEntity"
]
