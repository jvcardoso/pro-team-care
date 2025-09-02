"""
User DTOs - Commands para operações de usuário
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CreateUserCommand:
    """Command para criação de usuário"""
    email: str
    password: str
    person_id: int
    is_system_admin: bool = False
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class UpdateUserCommand:
    """Command para atualização de usuário"""
    user_id: int
    email: Optional[str] = None
    person_id: Optional[int] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class AuthenticateUserCommand:
    """Command para autenticação de usuário"""
    email: str
    password: str
    remember_me: bool = False