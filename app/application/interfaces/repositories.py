"""
Repository Interfaces - Contratos para persistência
Application Layer define o que precisa, Infrastructure implementa
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.entities import User
from app.domain.entities.company import CompanyEntity


class UserRepositoryInterface(ABC):
    """Interface para operações de usuário"""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuário por ID"""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""

    @abstractmethod
    async def create(self, user_data: dict) -> User:
        """Criar novo usuário"""

    @abstractmethod
    async def update(self, user_id: int, user_data: dict) -> User:
        """Atualizar usuário existente"""


class CompanyRepositoryInterface(ABC):
    """Interface para operações de empresa - ✅ Usando entidades puras do Domain"""

    @abstractmethod
    async def get_by_id(self, company_id: int) -> Optional[CompanyEntity]:
        """Buscar empresa por ID"""

    @abstractmethod
    async def get_by_cnpj(self, cnpj: str) -> Optional[CompanyEntity]:
        """Buscar empresa por CNPJ"""

    @abstractmethod
    async def create(self, company_data: CompanyEntity) -> CompanyEntity:
        """Criar nova empresa"""

    @abstractmethod
    async def update(
        self, company_id: int, company_data: Dict[str, Any]
    ) -> CompanyEntity:
        """Atualizar empresa existente"""

    @abstractmethod
    async def delete(self, company_id: int) -> None:
        """Deletar empresa (soft delete)"""

    @abstractmethod
    async def search(self, filters: Dict[str, Any]) -> List[CompanyEntity]:
        """Buscar empresas por filtros"""

    @abstractmethod
    async def exists_by_cnpj(self, cnpj: str) -> bool:
        """Verificar se CNPJ já existe"""
