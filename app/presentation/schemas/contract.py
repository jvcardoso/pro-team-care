from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContractType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    CORPORATIVO = "CORPORATIVO"
    EMPRESARIAL = "EMPRESARIAL"


class ContractStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"  # Match database
    EXPIRED = "expired"      # Match database


class PaymentFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"


class ServiceCategory(str, Enum):
    ENFERMAGEM = "ENFERMAGEM"
    FISIOTERAPIA = "FISIOTERAPIA"
    MEDICINA = "MEDICINA"
    EQUIPAMENTO = "EQUIPAMENTO"
    NUTRICAO = "NUTRIÇÃO"
    PSICOLOGIA = "PSICOLOGIA"


class ServiceType(str, Enum):
    PROCEDIMENTO = "PROCEDIMENTO"
    CONSULTA = "CONSULTA"
    EXAME = "EXAME"
    TERAPIA = "TERAPIA"
    LOCACAO = "LOCAÇÃO"


class PriorityLevel(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


# ==========================================
# SERVICES SCHEMAS
# ==========================================


class ServicesCatalogBase(BaseModel):
    service_code: str = Field(..., max_length=20)
    service_name: str = Field(..., max_length=100)
    service_category: ServiceCategory
    service_type: ServiceType
    requires_prescription: bool = False
    requires_specialist: bool = False  # Added from database
    home_visit_required: bool = True
    default_unit_value: Optional[Decimal] = None
    billing_unit: str = Field(default="UNIT", max_length=20)  # Added from database
    anvisa_regulated: bool = False  # Added from database
    requires_authorization: bool = False  # Added from database
    description: Optional[str] = None
    instructions: Optional[str] = None  # Added from database
    contraindications: Optional[str] = None  # Added from database


class ServicesCatalogCreate(ServicesCatalogBase):
    pass


class ServicesCatalogUpdate(BaseModel):
    service_name: Optional[str] = Field(None, max_length=100)
    service_category: Optional[ServiceCategory] = None
    service_type: Optional[ServiceType] = None
    requires_prescription: Optional[bool] = None
    requires_specialist: Optional[bool] = None
    home_visit_required: Optional[bool] = None
    default_unit_value: Optional[Decimal] = None
    billing_unit: Optional[str] = Field(None, max_length=20)
    anvisa_regulated: Optional[bool] = None
    requires_authorization: Optional[bool] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    contraindications: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class ServicesCatalogResponse(ServicesCatalogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime


# ==========================================
# CONTRACT SCHEMAS
# ==========================================


class ContractBase(BaseModel):
    client_id: int
    contract_type: ContractType = ContractType.INDIVIDUAL
    plan_name: str = Field(..., min_length=1, max_length=100)
    lives_contracted: int = Field(1, ge=1)
    lives_minimum: Optional[int] = None
    lives_maximum: Optional[int] = None
    allows_substitution: bool = False
    start_date: date
    end_date: Optional[date] = None
    monthly_value: Optional[Decimal] = None
    control_period: str = "MONTHLY"  # Matches database field
    service_address_type: Optional[str] = Field("PATIENT", max_length=10)
    service_addresses: Optional[Dict[str, Any]] = None  # JSON field in database
    status: ContractStatus = ContractStatus.ACTIVE
    notes: Optional[str] = None  # Field para observações do contrato

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        if v and info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("lives_minimum", "lives_maximum")
    @classmethod
    def validate_lives_limits(cls, v, info):
        if v and v < 1:
            raise ValueError("Lives limits must be positive")
        lives_contracted = info.data.get("lives_contracted", 1)
        if v and v > lives_contracted * 2:  # Reasonable upper limit
            raise ValueError("Lives limits seem unrealistic")
        return v


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_type: Optional[ContractType] = None
    plan_name: Optional[str] = Field(None, min_length=1, max_length=100)
    lives_contracted: Optional[int] = Field(None, ge=1)
    lives_minimum: Optional[int] = None
    lives_maximum: Optional[int] = None
    allows_substitution: Optional[bool] = None
    end_date: Optional[date] = None
    monthly_value: Optional[Decimal] = None
    control_period: Optional[str] = None
    service_address_type: Optional[str] = Field(None, max_length=10)
    service_addresses: Optional[Dict[str, Any]] = None
    status: Optional[ContractStatus] = None
    notes: Optional[str] = None  # Field para observações do contrato


class ContractResponse(ContractBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_number: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


class ContractDetailed(ContractResponse):
    # Related data will be added as we build the relationships
    pass


# ==========================================
# CONTRACT LIVES SCHEMAS
# ==========================================


class ContractLiveBase(BaseModel):
    contract_id: int
    person_id: int
    start_date: date
    end_date: Optional[date] = None
    relationship_type: str = Field(..., max_length=20)  # From database: TITULAR, DEPENDENTE, FUNCIONARIO, BENEFICIARIO
    status: str = Field(default="active", max_length=20)  # From database: ACTIVE, INACTIVE, SUBSTITUTED, CANCELLED
    substitution_reason: Optional[str] = Field(None, max_length=100)
    primary_service_address: Optional[Dict[str, Any]] = None  # JSON field


class ContractLiveCreate(ContractLiveBase):
    pass


class ContractLiveUpdate(BaseModel):
    end_date: Optional[date] = None
    relationship_type: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    substitution_reason: Optional[str] = Field(None, max_length=100)
    primary_service_address: Optional[Dict[str, Any]] = None


class ContractLiveResponse(ContractLiveBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ==========================================
# CONTRACT SERVICES SCHEMAS
# ==========================================


class ContractServiceBase(BaseModel):
    contract_id: int
    service_id: int
    monthly_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    annual_limit: Optional[int] = None
    unit_value: Optional[Decimal] = None  # Changed from unit_value_override to match database
    requires_pre_authorization: bool = False  # Added from database
    start_date: date
    end_date: Optional[date] = None
    status: str = Field(default="active", max_length=20)


class ContractServiceCreate(ContractServiceBase):
    pass


class ContractServiceUpdate(BaseModel):
    monthly_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    annual_limit: Optional[int] = None
    unit_value: Optional[Decimal] = None
    requires_pre_authorization: Optional[bool] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)


class ContractServiceResponse(ContractServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


# ==========================================
# CONTRACT LIFE SERVICES SCHEMAS
# ==========================================


class ContractLifeServiceBase(BaseModel):
    contract_life_id: int
    service_id: int
    is_authorized: bool = True
    authorization_date: Optional[date] = None
    monthly_limit_override: Optional[int] = None
    daily_limit_override: Optional[int] = None
    annual_limit_override: Optional[int] = None
    medical_indication: Optional[str] = None
    contraindications: Optional[str] = None
    special_instructions: Optional[str] = None
    priority_level: PriorityLevel = PriorityLevel.NORMAL
    start_date: date
    end_date: Optional[date] = None
    status: ContractStatus = ContractStatus.ACTIVE


class ContractLifeServiceCreate(ContractLifeServiceBase):
    pass


class ContractLifeServiceUpdate(BaseModel):
    is_authorized: Optional[bool] = None
    authorization_date: Optional[date] = None
    monthly_limit_override: Optional[int] = None
    daily_limit_override: Optional[int] = None
    annual_limit_override: Optional[int] = None
    medical_indication: Optional[str] = None
    contraindications: Optional[str] = None
    special_instructions: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None
    end_date: Optional[date] = None
    status: Optional[ContractStatus] = None


class ContractLifeServiceResponse(ContractLifeServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    authorized_by: Optional[int] = None
    created_by: Optional[int] = None


# ==========================================
# SERVICE EXECUTION SCHEMAS
# ==========================================


class ServiceExecutionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ServiceExecutionBase(BaseModel):
    contract_life_id: int
    service_id: int
    professional_id: Optional[int] = None
    execution_date: datetime  # Changed to datetime to match database
    quantity: Optional[Decimal] = Field(default=1)  # Added from database
    unit_value: Decimal  # Made required to match database
    total_value: Optional[Decimal] = None  # Added from database
    service_address: Optional[Dict[str, Any]] = None  # Added from database
    arrival_time: Optional[datetime] = None  # Added from database
    departure_time: Optional[datetime] = None  # Added from database
    duration_minutes: Optional[int] = None
    execution_notes: Optional[str] = None  # Changed from observations
    patient_response: Optional[str] = None  # Added from database
    complications: Optional[str] = None  # Added from database
    materials_used: Optional[Dict[str, Any]] = None  # Added from database
    quality_score: Optional[int] = Field(None, ge=1, le=5)  # Changed from patient_satisfaction
    family_satisfaction: Optional[int] = Field(None, ge=1, le=5)  # Added from database
    status: str = Field(default="scheduled", max_length=20)  # Changed to str
    cancellation_reason: Optional[str] = None  # Added from database


class ServiceExecutionCreate(ServiceExecutionBase):
    pass


class ServiceExecutionUpdate(BaseModel):
    professional_id: Optional[int] = None
    execution_date: Optional[datetime] = None
    quantity: Optional[Decimal] = None
    unit_value: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    service_address: Optional[Dict[str, Any]] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    execution_notes: Optional[str] = None
    patient_response: Optional[str] = None
    complications: Optional[str] = None
    materials_used: Optional[Dict[str, Any]] = None
    quality_score: Optional[int] = Field(None, ge=1, le=5)
    family_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = Field(None, max_length=20)
    cancellation_reason: Optional[str] = None


class ServiceExecutionResponse(ServiceExecutionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


# ==========================================
# LIST PARAMETERS
# ==========================================


class ContractListParams(BaseModel):
    client_id: Optional[int] = None
    status: Optional[ContractStatus] = None
    contract_type: Optional[ContractType] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class ServicesListParams(BaseModel):
    category: Optional[ServiceCategory] = None
    service_type: Optional[ServiceType] = None
    page: int = Field(1, ge=1)
    size: int = Field(100, ge=1, le=500)


# ==========================================
# RESPONSE CONTAINERS
# ==========================================


class ContractListResponse(BaseModel):
    contracts: List[ContractResponse]
    total: int
    page: int
    size: int
    pages: int


class ServicesListResponse(BaseModel):
    services: List[ServicesCatalogResponse]
    total: int
    page: int
    size: int
    pages: int