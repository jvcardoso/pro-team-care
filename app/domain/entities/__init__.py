"""
Domain Entities - Clean Architecture
Entidades puras de domínio sem dependências de frameworks
"""

from .company import (
    AccessDifficulty,
    AddressEntity,
    AddressType,
    CompanyEntity,
    EmailEntity,
    EmailType,
    LineType,
    PeopleEntity,
    PersonStatus,
    PersonType,
    PhoneEntity,
    PhoneType,
)
from .user import User

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
    "CompanyEntity",
]
