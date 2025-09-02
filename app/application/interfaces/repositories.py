"""
Repository Interfaces - Contratos para persistência
Application Layer define o que precisa, Infrastructure implementa
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.domain.entities import User
from app.domain.entities.company import CompanyEntity


class UserRepositoryInterface(ABC):
    """Interface para operações de usuário"""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuário por ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        pass
    
    @abstractmethod
    async def create(self, user_data: dict) -> User:
        """Criar novo usuário"""
        pass
    
    @abstractmethod
    async def update(self, user_id: int, user_data: dict) -> User:
        """Atualizar usuário existente"""
        pass


class CompanyRepositoryInterface(ABC):
    """Interface para operações de empresa - ✅ Usando entidades puras do Domain"""
    
    @abstractmethod
    async def get_by_id(self, company_id: int) -> Optional[CompanyEntity]:
        """Buscar empresa por ID"""
        pass
    
    @abstractmethod  
    async def get_by_cnpj(self, cnpj: str) -> Optional[CompanyEntity]:
        """Buscar empresa por CNPJ"""
        pass
    
    @abstractmethod
    async def create(self, company_data: CompanyEntity) -> CompanyEntity:
        """Criar nova empresa"""
        pass
    
    @abstractmethod
    async def update(self, company_id: int, company_data: Dict[str, Any]) -> CompanyEntity:
        """Atualizar empresa existente"""
        pass
    
    @abstractmethod
    async def delete(self, company_id: int) -> None:
        """Deletar empresa (soft delete)"""
        pass
    
    @abstractmethod
    async def search(self, filters: Dict[str, Any]) -> List[CompanyEntity]:
        """Buscar empresas por filtros"""
        pass
    
    @abstractmethod
    async def exists_by_cnpj(self, cnpj: str) -> bool:
        """Verificar se CNPJ já existe"""
        pass