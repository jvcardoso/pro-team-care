"""
Schemas Pydantic para sistema de controle de limites automático
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class LimitType(str, Enum):
    """Tipos de limite"""
    SESSIONS = "sessions"
    FINANCIAL = "financial"
    FREQUENCY = "frequency"


class EntityType(str, Enum):
    """Tipos de entidade"""
    AUTHORIZATION = "authorization"
    CONTRACT = "contract"
    SERVICE = "service"
    GLOBAL = "global"


class ViolationType(str, Enum):
    """Tipos de violação"""
    SESSIONS_EXCEEDED = "sessions_exceeded"
    FINANCIAL_EXCEEDED = "financial_exceeded"
    FREQUENCY_EXCEEDED = "frequency_exceeded"
    AUTHORIZATION_EXPIRED = "authorization_expired"
    CONTRACT_LIMIT_EXCEEDED = "contract_limit_exceeded"


class AlertType(str, Enum):
    """Tipos de alerta"""
    LIMIT_WARNING = "limit_warning"
    EXPIRY_WARNING = "expiry_warning"
    VIOLATION_DETECTED = "violation_detected"
    USAGE_THRESHOLD = "usage_threshold"


class AlertSeverity(str, Enum):
    """Níveis de severidade de alerta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# === LIMITS CONFIGURATION SCHEMAS ===

class LimitsConfigurationBase(BaseModel):
    """Schema base para configuração de limites"""
    limit_type: LimitType
    entity_type: EntityType
    entity_id: Optional[int] = None
    limit_value: float = Field(..., gt=0, description="Valor do limite")
    limit_period: Optional[str] = Field(None, description="Período do limite (daily, weekly, monthly)")
    description: Optional[str] = None
    override_allowed: bool = False
    is_active: bool = True


class LimitsConfigurationCreate(LimitsConfigurationBase):
    """Schema para criação de configuração de limites"""
    pass


class LimitsConfigurationUpdate(BaseModel):
    """Schema para atualização de configuração de limites"""
    limit_value: Optional[float] = Field(None, gt=0)
    limit_period: Optional[str] = None
    description: Optional[str] = None
    override_allowed: Optional[bool] = None
    is_active: Optional[bool] = None


class LimitsConfiguration(LimitsConfigurationBase):
    """Schema completo para configuração de limites"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === SERVICE USAGE TRACKING SCHEMAS ===

class ServiceUsageTrackingBase(BaseModel):
    """Schema base para rastreamento de uso de serviços"""
    authorization_id: int
    sessions_used: int = Field(..., gt=0, description="Número de sessões utilizadas")
    execution_date: date
    notes: Optional[str] = None


class ServiceUsageTrackingCreate(ServiceUsageTrackingBase):
    """Schema para criação de rastreamento de uso"""
    executed_by: int


class ServiceUsageTracking(ServiceUsageTrackingBase):
    """Schema completo para rastreamento de uso"""
    id: int
    executed_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# === LIMITS VIOLATION SCHEMAS ===

class LimitsViolationBase(BaseModel):
    """Schema base para violação de limites"""
    authorization_id: int
    violation_type: ViolationType
    attempted_value: float
    limit_value: float
    description: str


class LimitsViolationCreate(LimitsViolationBase):
    """Schema para criação de violação de limites"""
    detected_by: int


class LimitsViolation(LimitsViolationBase):
    """Schema completo para violação de limites"""
    id: int
    detected_by: int
    detected_at: datetime

    class Config:
        from_attributes = True


# === ALERTS CONFIGURATION SCHEMAS ===

class AlertsConfigurationBase(BaseModel):
    """Schema base para configuração de alertas"""
    alert_type: AlertType
    entity_type: EntityType
    entity_id: Optional[int] = None
    threshold_value: Optional[float] = Field(None, ge=0)
    threshold_percentage: Optional[float] = Field(None, ge=0, le=100)
    message_template: str
    is_active: bool = True

    @validator('threshold_value', 'threshold_percentage')
    def at_least_one_threshold(cls, v, values):
        """Pelo menos um threshold deve ser definido"""
        if 'threshold_value' in values and not values['threshold_value'] and not v:
            raise ValueError('Pelo menos um threshold (value ou percentage) deve ser definido')
        return v


class AlertsConfigurationCreate(AlertsConfigurationBase):
    """Schema para criação de configuração de alertas"""
    pass


class AlertsConfigurationUpdate(BaseModel):
    """Schema para atualização de configuração de alertas"""
    threshold_value: Optional[float] = Field(None, ge=0)
    threshold_percentage: Optional[float] = Field(None, ge=0, le=100)
    message_template: Optional[str] = None
    is_active: Optional[bool] = None


class AlertsConfiguration(AlertsConfigurationBase):
    """Schema completo para configuração de alertas"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === ALERTS LOG SCHEMAS ===

class AlertsLogBase(BaseModel):
    """Schema base para log de alertas"""
    entity_id: int
    message: str
    severity: AlertSeverity = AlertSeverity.MEDIUM
    data: Optional[Dict[str, Any]] = None


class AlertsLogCreate(AlertsLogBase):
    """Schema para criação de log de alertas"""
    alert_config_id: int


class AlertsLog(AlertsLogBase):
    """Schema completo para log de alertas"""
    id: int
    alert_config_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# === REQUEST/RESPONSE SCHEMAS ===

class CheckLimitsRequest(BaseModel):
    """Schema para requisição de verificação de limites"""
    authorization_id: int
    sessions_to_use: int = Field(1, gt=0)
    execution_date: Optional[date] = None


class CheckLimitsResponse(BaseModel):
    """Schema para resposta de verificação de limites"""
    allowed: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    current_usage: Dict[str, Any]
    limits: Dict[str, Any]


class UsageStatistics(BaseModel):
    """Schema para estatísticas de uso"""
    total_executions: int
    total_sessions: int
    avg_sessions_per_execution: float
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class LimitsDashboard(BaseModel):
    """Schema para dashboard de limites"""
    period: Dict[str, date]
    violations: Dict[str, int]
    usage: Dict[str, int]
    alerts: Dict[str, int]
    expiring_authorizations: List[Dict[str, Any]]
    recent_violations: List[LimitsViolation]


class ExpiringAuthorizationAlert(BaseModel):
    """Schema para alerta de autorização expirando"""
    authorization_id: int
    authorization_code: str
    valid_until: date
    sessions_remaining: Optional[int]
    service_name: str
    patient_name: str
    contract_number: str
    days_until_expiry: int


# === LIST RESPONSES ===

class LimitsConfigurationListParams(BaseModel):
    """Parâmetros para listagem de configurações de limite"""
    limit_type: Optional[LimitType] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[int] = None
    is_active: Optional[bool] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class LimitsConfigurationListResponse(BaseModel):
    """Resposta para listagem de configurações de limite"""
    configurations: List[LimitsConfiguration]
    total: int
    page: int
    size: int
    pages: int


class ServiceUsageTrackingListParams(BaseModel):
    """Parâmetros para listagem de rastreamento de uso"""
    authorization_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class ServiceUsageTrackingListResponse(BaseModel):
    """Resposta para listagem de rastreamento de uso"""
    usages: List[ServiceUsageTracking]
    total: int
    page: int
    size: int
    pages: int


class LimitsViolationListParams(BaseModel):
    """Parâmetros para listagem de violações"""
    authorization_id: Optional[int] = None
    violation_type: Optional[ViolationType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class LimitsViolationListResponse(BaseModel):
    """Resposta para listagem de violações"""
    violations: List[LimitsViolation]
    total: int
    page: int
    size: int
    pages: int


class AlertsLogListParams(BaseModel):
    """Parâmetros para listagem de logs de alerta"""
    entity_id: Optional[int] = None
    severity: Optional[AlertSeverity] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class AlertsLogListResponse(BaseModel):
    """Resposta para listagem de logs de alerta"""
    logs: List[AlertsLog]
    total: int
    page: int
    size: int
    pages: int