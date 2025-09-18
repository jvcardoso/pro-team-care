"""
Service Interfaces - Contratos para serviços de domínio
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, List, Optional


class AddressEnrichmentServiceInterface(ABC):
    """Interface para enriquecimento de endereços"""

    @abstractmethod
    async def enrich_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer um endereço com ViaCEP e geocoding"""

    @abstractmethod
    async def enrich_multiple_addresses(
        self, addresses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enriquecer múltiplos endereços"""


class EmailServiceInterface(ABC):
    """Interface para serviços de email"""

    @abstractmethod
    async def send_notification(self, to: str, subject: str, content: str) -> bool:
        """Enviar notificação por email"""

    @abstractmethod
    async def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Enviar email de boas-vindas"""


class CacheServiceInterface(ABC):
    """Interface para serviços de cache"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Buscar item no cache"""

    @abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Armazenar item no cache"""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remover item do cache"""

    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidar itens por padrão"""


class AuthServiceInterface(ABC):
    """Interface para serviços de autenticação - ✅ Clean Architecture"""

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar senha"""

    @abstractmethod
    def get_password_hash(self, password: str) -> str:
        """Gerar hash da senha"""

    @abstractmethod
    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Criar token de acesso"""
