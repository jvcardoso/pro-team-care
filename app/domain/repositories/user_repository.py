from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import UserEntity


class UserRepositoryInterface(ABC):
    """Interface para repositório de usuários"""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Buscar usuário por ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Buscar usuário por email"""
        pass
    
    @abstractmethod
    async def create(self, user_data: dict) -> UserEntity:
        """Criar novo usuário"""
        pass
    
    @abstractmethod
    async def update(self, user_id: int, user_data: dict) -> Optional[UserEntity]:
        """Atualizar usuário"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Deletar usuário"""
        pass