"""Schemas para autorizações médicas"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class UrgencyLevelEnum(str, Enum):
    """Níveis de urgência"""
    URGENT = "URGENT"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class AuthorizationStatusEnum(str, Enum):
    """Status das autorizações"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class AuthorizationActionEnum(str, Enum):
    """Ações do histórico de autorizações"""
    CREATED = "created"
    UPDATED = "updated"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    RENEWED = "renewed"
    SESSIONS_UPDATED = "sessions_updated"


# Base schemas
class MedicalAuthorizationBase(BaseModel):
    """Schema base para autorizações médicas"""
    contract_life_id: int = Field(..., description="ID da vida do contrato")
    service_id: int = Field(..., description="ID do serviço")
    doctor_id: int = Field(..., description="ID do médico")
    authorization_date: date = Field(..., description="Data da autorização")
    valid_from: date = Field(..., description="Válido a partir de")
    valid_until: date = Field(..., description="Válido até")

    # Session limits
    sessions_authorized: Optional[int] = Field(None, description="Total de sessões autorizadas")
    sessions_remaining: Optional[int] = Field(None, description="Sessões restantes")
    monthly_limit: Optional[int] = Field(None, description="Limite mensal")
    weekly_limit: Optional[int] = Field(None, description="Limite semanal")
    daily_limit: Optional[int] = Field(None, description="Limite diário")

    # Medical information
    medical_indication: str = Field(..., description="Indicação médica")
    contraindications: Optional[str] = Field(None, description="Contraindicações")
    special_instructions: Optional[str] = Field(None, description="Instruções especiais")
    urgency_level: UrgencyLevelEnum = Field(UrgencyLevelEnum.NORMAL, description="Nível de urgência")
    requires_supervision: bool = Field(False, description="Requer supervisão")
    supervision_notes: Optional[str] = Field(None, description="Notas de supervisão")
    diagnosis_cid: Optional[str] = Field(None, description="Código CID-10")
    diagnosis_description: Optional[str] = Field(None, description="Descrição do diagnóstico")
    treatment_goals: Optional[str] = Field(None, description="Objetivos do tratamento")
    expected_duration_days: Optional[int] = Field(None, description="Duração esperada em dias")

    # Renewal
    renewal_allowed: bool = Field(True, description="Permite renovação")
    renewal_conditions: Optional[str] = Field(None, description="Condições para renovação")

    @validator('valid_until')
    def validate_date_range(cls, v, values):
        if 'valid_from' in values and v < values['valid_from']:
            raise ValueError('Data final deve ser posterior à data inicial')
        return v

    @validator('sessions_remaining')
    def validate_sessions(cls, v, values):
        if v is not None and 'sessions_authorized' in values and values['sessions_authorized'] is not None:
            if v > values['sessions_authorized']:
                raise ValueError('Sessões restantes não podem ser maiores que autorizadas')
        return v


class MedicalAuthorizationCreate(MedicalAuthorizationBase):
    """Schema para criação de autorização médica"""
    pass


class MedicalAuthorizationUpdate(BaseModel):
    """Schema para atualização de autorização médica"""
    authorization_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    sessions_authorized: Optional[int] = None
    sessions_remaining: Optional[int] = None
    monthly_limit: Optional[int] = None
    weekly_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    medical_indication: Optional[str] = None
    contraindications: Optional[str] = None
    special_instructions: Optional[str] = None
    urgency_level: Optional[UrgencyLevelEnum] = None
    requires_supervision: Optional[bool] = None
    supervision_notes: Optional[str] = None
    diagnosis_cid: Optional[str] = None
    diagnosis_description: Optional[str] = None
    treatment_goals: Optional[str] = None
    expected_duration_days: Optional[int] = None
    renewal_allowed: Optional[bool] = None
    renewal_conditions: Optional[str] = None


class MedicalAuthorizationCancel(BaseModel):
    """Schema para cancelamento de autorização"""
    cancellation_reason: str = Field(..., description="Motivo do cancelamento")


class MedicalAuthorizationInDB(MedicalAuthorizationBase):
    """Schema de autorização médica no banco"""
    id: int
    authorization_code: str
    status: AuthorizationStatusEnum
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        orm_mode = True


class MedicalAuthorizationResponse(MedicalAuthorizationInDB):
    """Schema de resposta com dados relacionados"""
    service_name: Optional[str] = None
    service_category: Optional[str] = None
    service_type: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_email: Optional[str] = None
    patient_name: Optional[str] = None
    contract_number: Optional[str] = None


# Authorization Renewal schemas
class AuthorizationRenewalBase(BaseModel):
    """Schema base para renovações"""
    original_authorization_id: int
    new_authorization_id: int
    renewal_date: date
    renewal_reason: Optional[str] = None
    changes_made: Optional[str] = None


class AuthorizationRenewalCreate(AuthorizationRenewalBase):
    """Schema para criação de renovação"""
    pass


class AuthorizationRenewalInDB(AuthorizationRenewalBase):
    """Schema de renovação no banco"""
    id: int
    approved_by: int
    created_at: datetime

    class Config:
        orm_mode = True


class AuthorizationRenewalResponse(AuthorizationRenewalInDB):
    """Schema de resposta de renovação"""
    approved_by_name: Optional[str] = None
    original_authorization_code: Optional[str] = None
    new_authorization_code: Optional[str] = None


# Authorization History schemas
class AuthorizationHistoryBase(BaseModel):
    """Schema base para histórico"""
    authorization_id: int
    action: AuthorizationActionEnum
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None


class AuthorizationHistoryCreate(AuthorizationHistoryBase):
    """Schema para criação de histórico"""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuthorizationHistoryInDB(AuthorizationHistoryBase):
    """Schema de histórico no banco"""
    id: int
    performed_by: int
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        orm_mode = True


class AuthorizationHistoryResponse(AuthorizationHistoryInDB):
    """Schema de resposta de histórico"""
    performed_by_name: Optional[str] = None
    authorization_code: Optional[str] = None


# List responses
class MedicalAuthorizationListParams(BaseModel):
    """Parâmetros para listagem de autorizações"""
    contract_life_id: Optional[int] = None
    service_id: Optional[int] = None
    doctor_id: Optional[int] = None
    status: Optional[AuthorizationStatusEnum] = None
    urgency_level: Optional[UrgencyLevelEnum] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    requires_supervision: Optional[bool] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class MedicalAuthorizationListResponse(BaseModel):
    """Resposta de listagem de autorizações"""
    authorizations: List[MedicalAuthorizationResponse]
    total: int
    page: int
    size: int
    pages: int


# Statistics
class AuthorizationStatistics(BaseModel):
    """Estatísticas de autorizações"""
    total_authorizations: int
    active_authorizations: int
    expired_authorizations: int
    cancelled_authorizations: int
    suspended_authorizations: int
    urgent_authorizations: int
    authorizations_requiring_supervision: int
    sessions_authorized_total: int
    sessions_remaining_total: int
    average_duration_days: Optional[float] = None
    most_common_service: Optional[str] = None
    most_active_doctor: Optional[str] = None


# Quick actions
class SessionUpdateRequest(BaseModel):
    """Atualização de sessões utilizadas"""
    sessions_used: int = Field(..., ge=1, description="Número de sessões utilizadas")
    notes: Optional[str] = Field(None, description="Observações sobre a utilização")


class AuthorizationSuspendRequest(BaseModel):
    """Suspensão de autorização"""
    reason: str = Field(..., description="Motivo da suspensão")
    suspension_until: Optional[date] = Field(None, description="Suspender até data específica")


class AuthorizationRenewRequest(BaseModel):
    """Renovação de autorização"""
    new_valid_until: date = Field(..., description="Nova data de validade")
    additional_sessions: Optional[int] = Field(None, description="Sessões adicionais")
    renewal_reason: str = Field(..., description="Motivo da renovação")
    changes_summary: Optional[str] = Field(None, description="Resumo das alterações")