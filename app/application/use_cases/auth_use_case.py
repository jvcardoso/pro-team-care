from datetime import timedelta
from typing import Optional, Dict, Any

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.application.interfaces.services import AuthServiceInterface
# ✅ Application Layer não deve depender de Presentation - apenas de Domain
from config.settings import settings


class AuthUseCase:
    """Use case para autenticação - ✅ Clean Architecture"""
    
    def __init__(self, user_repository: UserRepositoryInterface, auth_service: AuthServiceInterface):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autenticar usuário com email e senha"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None
        
        if not self.auth_service.verify_password(password, user.password):
            return None
        
        return user
    
    async def create_access_token_for_user(self, user: User) -> Dict[str, str]:
        """Criar token de acesso para usuário - ✅ Retorna dict básico"""
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = self.auth_service.create_access_token(
            data={"sub": user.email_address}, 
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """Registrar novo usuário - ✅ Recebe e retorna dados básicos"""
        # Verificar se usuário já existe
        existing_user = await self.user_repository.get_by_email(user_data["email"])
        if existing_user:
            raise ValueError("User already exists")
        
        # Hash da senha
        hashed_password = self.auth_service.get_password_hash(user_data["password"])
        
        # Criar usuário
        user_entity = await self.user_repository.create({
            "email_address": user_data["email"],
            "password": hashed_password,
            "is_active": user_data.get("is_active", True),
            "is_system_admin": user_data.get("is_superuser", False),
            "person_id": 1  # TODO: Implementar lógica adequada para person_id
        })
        
        return user_entity
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email - ✅ Retorna entidade pura"""
        return await self.user_repository.get_by_email(email)