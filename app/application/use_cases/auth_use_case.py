from datetime import timedelta
from typing import Optional

from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.auth import verify_password, get_password_hash, create_access_token
from app.domain.models.user import UserCreate, User, Token
from config.settings import settings


class AuthUseCase:
    """Use case para autenticação"""
    
    def __init__(self, user_repository: UserRepositoryInterface):
        self.user_repository = user_repository
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserEntity]:
        """Autenticar usuário com email e senha"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return user
    
    async def create_access_token_for_user(self, user: UserEntity) -> Token:
        """Criar token de acesso para usuário"""
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email_address}, 
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Registrar novo usuário"""
        # Verificar se usuário já existe
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User already exists")
        
        # Hash da senha
        hashed_password = get_password_hash(user_data.password)
        
        # Criar usuário
        user_entity = await self.user_repository.create({
            "email_address": user_data.email,  # Corrigido: usar email_address
            "password": hashed_password,       # Corrigido: usar password ao invés de hashed_password
            "is_active": user_data.is_active,
            "is_system_admin": user_data.is_superuser,  # Corrigido: mapear para is_system_admin
            "person_id": 1  # TODO: Implementar lógica adequada para person_id
        })
        
        # Converter para modelo Pydantic
        return User(
            id=user_entity.id,
            email=user_entity.email_address,  # Corrigido: usar email_address
            full_name="N/A",  # TODO: Implementar mapeamento adequado ou buscar de tabela Person
            is_active=user_entity.is_active,
            is_superuser=user_entity.is_system_admin,  # Corrigido: mapear de is_system_admin
            created_at=user_entity.created_at
        )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        user_entity = await self.user_repository.get_by_email(email)
        if not user_entity:
            return None
        
        return User(
            id=user_entity.id,
            email=user_entity.email_address,  # Corrigido: usar email_address
            full_name="N/A",  # TODO: Implementar mapeamento adequado ou buscar de tabela Person
            is_active=user_entity.is_active,
            is_superuser=user_entity.is_system_admin,  # Corrigido: mapear de is_system_admin
            created_at=user_entity.created_at
        )