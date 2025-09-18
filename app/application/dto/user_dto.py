"""
User DTOs - Commands e schemas para operações de usuário com ativação
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


# Commands originais
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


# Novos schemas para ativação de usuários
class UserBase(BaseModel):
    """Dados base do usuário"""

    email_address: EmailStr
    context_type: str = Field(
        ..., description="Tipo de contexto: company, establishment, client"
    )


class UserCreateWithInvitation(UserBase):
    """Dados para criar usuário com convite"""

    company_id: Optional[int] = None
    establishment_id: Optional[int] = None
    invited_by_user_id: Optional[int] = None


class UserActivation(BaseModel):
    """Dados para ativação de usuário"""

    activation_token: str = Field(..., description="Token de ativação")
    password: str = Field(..., min_length=8, description="Nova senha do usuário")


class UserResponse(BaseModel):
    """Resposta com dados do usuário"""

    id: int
    email_address: str
    context_type: str
    status: str
    company_id: int
    establishment_id: Optional[int] = None
    created_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    invited_at: Optional[datetime] = None
    invited_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Dados para reset de senha"""

    email: EmailStr = Field(..., description="Email do usuário")


class PasswordResetConfirm(BaseModel):
    """Confirmação de reset de senha"""

    reset_token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=8, description="Nova senha")


class ResendActivation(BaseModel):
    """Reenvio de email de ativação"""

    user_id: int = Field(..., description="ID do usuário")


# Schemas para resposta dos formulários
class CompanyManagerInvite(BaseModel):
    """Convite para gestor de empresa"""

    email: EmailStr = Field(..., description="Email do gestor")
    company_id: int = Field(..., description="ID da empresa")


class EstablishmentManagerInvite(BaseModel):
    """Convite para gestor de estabelecimento"""

    email: EmailStr = Field(..., description="Email do gestor")
    establishment_id: int = Field(..., description="ID do estabelecimento")
