"""
Schemas Pydantic para processo de ativação de empresas

Este módulo define os schemas para o fluxo completo de ativação:
1. Envio de email de aceite de contrato
2. Aceite de contrato
3. Criação de usuário gestor
4. Ativação completa
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

# =====================================================
# REQUEST SCHEMAS
# =====================================================


class SendContractEmailRequest(BaseModel):
    """Request para enviar email de aceite de contrato"""

    company_id: int = Field(..., description="ID da empresa")
    recipient_email: EmailStr = Field(..., description="Email do destinatário")
    recipient_name: str = Field(
        ..., min_length=3, max_length=200, description="Nome do destinatário"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": 1,
                "recipient_email": "gestor@homecarebrasil.com.br",
                "recipient_name": "João Silva",
            }
        }


class AcceptContractRequest(BaseModel):
    """Request para aceitar contrato de uso"""

    contract_token: str = Field(
        ..., min_length=32, description="Token de aceite do contrato"
    )
    accepted_by_name: str = Field(
        ..., min_length=3, max_length=200, description="Nome de quem aceita"
    )
    accepted_by_email: EmailStr = Field(..., description="Email de quem aceita")
    accepted_by_cpf: Optional[str] = Field(
        None,
        min_length=11,
        max_length=11,
        description="CPF de quem aceita (apenas números)",
    )
    ip_address: str = Field(..., max_length=45, description="IP de origem (compliance)")
    terms_version: str = Field(default="1.0", description="Versão dos termos aceitos")

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Valida formato básico de IP"""
        import ipaddress

        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("IP address inválido")

    class Config:
        json_schema_extra = {
            "example": {
                "contract_token": "abc123def456ghi789jkl012mno345pq",
                "accepted_by_name": "João Silva",
                "accepted_by_email": "joao@homecarebrasil.com.br",
                "ip_address": "192.168.1.100",
                "terms_version": "1.0",
            }
        }


class SendUserCreationEmailRequest(BaseModel):
    """Request para enviar email de criação de usuário gestor"""

    company_id: int = Field(..., description="ID da empresa")
    email: EmailStr = Field(..., description="Email do futuro gestor")

    class Config:
        json_schema_extra = {
            "example": {"company_id": 1, "email": "gestor@homecarebrasil.com.br"}
        }


class ResendActivationEmailRequest(BaseModel):
    """Request para reenviar email de ativação"""

    company_id: int = Field(..., description="ID da empresa")

    class Config:
        json_schema_extra = {"example": {"company_id": 1}}


class ValidateActivationTokenRequest(BaseModel):
    """Request para validar token de ativação"""

    token: str = Field(..., min_length=32, description="Token de ativação")

    class Config:
        json_schema_extra = {"example": {"token": "abc123def456ghi789jkl012mno345pq"}}


# =====================================================
# RESPONSE SCHEMAS
# =====================================================


class CompanyActivationStatus(BaseModel):
    """Status detalhado de ativação de empresa"""

    company_id: int
    company_name: str
    access_status: Literal[
        "pending_contract", "contract_signed", "pending_user", "active", "suspended"
    ]

    # Contract info
    contract_sent: bool
    contract_sent_at: Optional[datetime] = None
    contract_sent_to: Optional[str] = None
    contract_accepted: bool
    contract_accepted_at: Optional[datetime] = None
    contract_accepted_by: Optional[str] = None
    contract_terms_version: Optional[str] = None

    # User info
    has_active_user: bool
    activated_at: Optional[datetime] = None
    activated_by_user_id: Optional[int] = None

    # Metrics
    days_since_creation: Optional[int] = None
    days_since_contract_sent: Optional[int] = None
    is_overdue: bool = False  # Mais de 7 dias sem ativação

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "company_id": 1,
                "company_name": "HOME CARE BRASIL",
                "access_status": "pending_contract",
                "contract_sent": False,
                "contract_sent_at": None,
                "contract_sent_to": None,
                "contract_accepted": False,
                "contract_accepted_at": None,
                "contract_accepted_by": None,
                "contract_terms_version": None,
                "has_active_user": False,
                "activated_at": None,
                "activated_by_user_id": None,
                "days_since_creation": 5,
                "days_since_contract_sent": None,
                "is_overdue": False,
            }
        }


class SendEmailResponse(BaseModel):
    """Response genérica para envio de emails"""

    success: bool
    message: str
    company_id: int
    sent_to: str
    sent_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email de aceite de contrato enviado com sucesso",
                "company_id": 1,
                "sent_to": "gestor@homecarebrasil.com.br",
                "sent_at": "2025-10-02T14:30:00",
            }
        }


class AcceptContractResponse(BaseModel):
    """Response para aceite de contrato"""

    success: bool
    message: str
    company_id: int
    access_status: str
    contract_accepted_at: datetime
    next_step: str  # Descrição do próximo passo

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Contrato aceito com sucesso",
                "company_id": 1,
                "access_status": "contract_signed",
                "contract_accepted_at": "2025-10-02T14:30:00",
                "next_step": "Email de criação de usuário enviado. Verifique sua caixa de entrada.",
            }
        }


class ValidateTokenResponse(BaseModel):
    """Response para validação de token"""

    valid: bool
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    token_type: Optional[str] = None  # 'contract', 'user_creation'
    expires_at: Optional[datetime] = None
    expired: bool = False
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "company_id": 1,
                "company_name": "HOME CARE BRASIL",
                "token_type": "contract",
                "expires_at": "2025-10-09T14:30:00",
                "expired": False,
                "error_message": None,
            }
        }


class CompanyActivationListResponse(BaseModel):
    """Lista de empresas com status de ativação"""

    total: int
    pending_contract: int
    contract_signed: int
    pending_user: int
    active: int
    suspended: int
    companies: list[CompanyActivationStatus]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "pending_contract": 3,
                "contract_signed": 2,
                "pending_user": 1,
                "active": 4,
                "suspended": 0,
                "companies": [],
            }
        }


# =====================================================
# INTERNAL SCHEMAS
# =====================================================


class ActivationTokenData(BaseModel):
    """Dados do token de ativação (interno)"""

    company_id: int
    token_type: Literal["contract", "user_creation"]
    email: str
    expires_at: datetime
    created_at: datetime


class CompanyActivationAudit(BaseModel):
    """Registro de auditoria de ativação (interno)"""

    company_id: int
    action: str
    performed_by: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    details: Optional[dict] = None

    class Config:
        from_attributes = True
