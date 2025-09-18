"""
Auth Service Implementation - Infrastructure Layer
"""

from datetime import timedelta
from typing import Optional

from app.application.interfaces.services import AuthServiceInterface
from app.infrastructure.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)


class AuthService(AuthServiceInterface):
    """Implementação do serviço de autenticação"""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar senha"""
        return verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Gerar hash da senha"""
        return get_password_hash(password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Criar token de acesso"""
        return create_access_token(data, expires_delta)
