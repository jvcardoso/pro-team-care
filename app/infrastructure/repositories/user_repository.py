from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.entities.user import UserEntity  # ORM model
from app.infrastructure.cache.decorators import cached, cache_invalidate
from app.infrastructure.monitoring.metrics import performance_metrics, track_performance


class UserRepository(UserRepositoryInterface):
    """Implementação concreta do repositório de usuários"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _orm_to_domain(self, user_orm: UserEntity) -> User:
        """Converter ORM model para domain entity"""
        return User(
            id=user_orm.id,
            person_id=user_orm.person_id,
            email_address=user_orm.email_address,
            password=user_orm.password,
            is_active=user_orm.is_active,
            is_system_admin=user_orm.is_system_admin,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
            email_verified_at=user_orm.email_verified_at,
            remember_token=user_orm.remember_token,
            preferences=user_orm.preferences,
            notification_settings=user_orm.notification_settings,
            two_factor_secret=user_orm.two_factor_secret,
            two_factor_recovery_codes=user_orm.two_factor_recovery_codes
        )
    
    def _domain_to_orm(self, user: User) -> UserEntity:
        """Converter domain entity para ORM model"""
        return UserEntity(
            id=user.id,
            person_id=user.person_id,
            email_address=user.email_address,
            is_active=user.is_active,
            is_system_admin=user.is_system_admin,
            email_verified_at=user.email_verified_at,
            remember_token=user.remember_token,
            preferences=user.preferences,
            notification_settings=user.notification_settings,
            two_factor_secret=user.two_factor_secret,
            two_factor_recovery_codes=user.two_factor_recovery_codes
        )
    
    @cached(ttl=300, key_prefix="user")  # Cache por 5 minutos
    @track_performance("get_by_id", "user_repository")
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Buscar usuário por ID"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        user_orm = result.scalar_one_or_none()
        return self._orm_to_domain(user_orm) if user_orm else None
    
    @cached(ttl=300, key_prefix="user")  # Cache por 5 minutos
    @track_performance("get_by_email", "user_repository")
    async def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.email_address == email)
        )
        user_orm = result.scalar_one_or_none()
        return self._orm_to_domain(user_orm) if user_orm else None
    
    @cache_invalidate("cache:func:*user*")  # Limpa todo cache de usuário
    @track_performance("create", "user_repository")
    async def create(self, user_data: dict) -> User:
        """Criar novo usuário"""
        user_orm = UserEntity(**user_data)
        self.session.add(user_orm)
        await self.session.commit()
        await self.session.refresh(user_orm)
        return self._orm_to_domain(user_orm)
    
    @cache_invalidate("cache:func:*user*")  # Limpa todo cache de usuário
    async def update(self, user_id: int, user_data: dict) -> Optional[User]:
        """Atualizar usuário"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        user_orm = result.scalar_one_or_none()
        if not user_orm:
            return None
        
        for key, value in user_data.items():
            if hasattr(user_orm, key):
                setattr(user_orm, key, value)
        
        await self.session.commit()
        await self.session.refresh(user_orm)
        return self._orm_to_domain(user_orm)
    
    @cache_invalidate("cache:func:*user*")  # Limpa todo cache de usuário
    async def delete(self, user_id: int) -> bool:
        """Deletar usuário"""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.id == user_id)
        )
        user_orm = result.scalar_one_or_none()
        if not user_orm:
            return False
        
        await self.session.delete(user_orm)
        await self.session.commit()
        return True