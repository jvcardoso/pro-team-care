from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import UserRepositoryInterface


class UserRepository(UserRepositoryInterface):
    """Implementação concreta do repositório de usuários"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Buscar usuário por ID"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Buscar usuário por email"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.email_address == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: dict) -> UserEntity:
        """Criar novo usuário"""
        user = UserEntity(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update(self, user_id: int, user_data: dict) -> Optional[UserEntity]:
        """Atualizar usuário"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Deletar usuário"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True