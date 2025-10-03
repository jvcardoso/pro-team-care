from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BillingCycle(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"


class InvoiceStatus(str, Enum):
    PENDENTE = "pendente"
    ENVIADA = "enviada"
    PAGA = "paga"
    VENCIDA = "vencida"
    CANCELADA = "cancelada"
    EM_ATRASO = "em_atraso"


class VerificationStatus(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    TRANSFERENCIA = "TRANSFERENCIA"
    TED = "TED"
    BOLETO = "BOLETO"
    CARTAO = "CARTAO"
    DINHEIRO = "DINHEIRO"
    DEPOSITO = "DEPOSITO"


# ==========================================
# CONTRACT BILLING SCHEDULE SCHEMAS
# ==========================================


class ContractBillingScheduleBase(BaseModel):
    contract_id: int
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    billing_day: int = Field(1, ge=1, le=31)
    next_billing_date: date
    amount_per_cycle: Decimal = Field(..., ge=0)
    is_active: bool = True

    @field_validator("next_billing_date")
    @classmethod
    def validate_next_billing_date(cls, v):
        if v < date.today():
            raise ValueError("Next billing date cannot be in the past")
        return v

    @field_validator("billing_day")
    @classmethod
    def validate_billing_day(cls, v, info):
        if v < 1 or v > 31:
            raise ValueError("Billing day must be between 1 and 31")
        return v


class ContractBillingScheduleCreate(ContractBillingScheduleBase):
    pass


class ContractBillingScheduleUpdate(BaseModel):
    billing_cycle: Optional[BillingCycle] = None
    billing_day: Optional[int] = Field(None, ge=1, le=31)
    next_billing_date: Optional[date] = None
    amount_per_cycle: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ContractBillingScheduleResponse(ContractBillingScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


# ==========================================
# CONTRACT INVOICE SCHEMAS
# ==========================================


class ContractInvoiceBase(BaseModel):
    contract_id: int
    billing_period_start: date
    billing_period_end: date
    lives_count: int = Field(..., ge=0)
    base_amount: Decimal = Field(..., ge=0)
    additional_services_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discounts: Decimal = Field(default=Decimal("0.00"), ge=0)
    taxes: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    status: InvoiceStatus = InvoiceStatus.PENDENTE
    due_date: date
    issued_date: date = Field(default_factory=date.today)
    paid_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_notes: Optional[str] = None
    observations: Optional[str] = None

    @field_validator("billing_period_end")
    @classmethod
    def validate_billing_period(cls, v, info):
        start_date = info.data.get("billing_period_start")
        if start_date and v <= start_date:
            raise ValueError("Billing period end must be after start date")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v, info):
        issued_date = info.data.get("issued_date", date.today())
        if v < issued_date:
            raise ValueError("Due date cannot be before issued date")
        return v

    @field_validator("paid_date")
    @classmethod
    def validate_paid_date(cls, v, info):
        if v and info.data.get("issued_date"):
            issued_date = info.data["issued_date"]
            if v < issued_date:
                raise ValueError("Paid date cannot be before issued date")
        return v

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v, info):
        # Auto-calculate total if not provided
        base_amount = info.data.get("base_amount", Decimal("0"))
        additional_services = info.data.get("additional_services_amount", Decimal("0"))
        discounts = info.data.get("discounts", Decimal("0"))
        taxes = info.data.get("taxes", Decimal("0"))

        calculated_total = base_amount + additional_services + taxes - discounts

        # Allow some tolerance for floating point precision
        if abs(v - calculated_total) > Decimal("0.01"):
            return calculated_total
        return v


class ContractInvoiceCreate(ContractInvoiceBase):
    invoice_number: Optional[str] = None  # Will be auto-generated if not provided


class ContractInvoiceUpdate(BaseModel):
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    lives_count: Optional[int] = Field(None, ge=0)
    base_amount: Optional[Decimal] = Field(None, ge=0)
    additional_services_amount: Optional[Decimal] = Field(None, ge=0)
    discounts: Optional[Decimal] = Field(None, ge=0)
    taxes: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_notes: Optional[str] = None
    observations: Optional[str] = None


class ContractInvoiceResponse(ContractInvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


class ContractInvoiceDetailed(ContractInvoiceResponse):
    # Will be expanded with related data
    receipts_count: Optional[int] = 0
    is_overdue: Optional[bool] = False
    days_overdue: Optional[int] = 0


# ==========================================
# PAYMENT RECEIPT SCHEMAS
# ==========================================


class PaymentReceiptBase(BaseModel):
    invoice_id: int
    file_name: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_type: Optional[str] = Field(None, max_length=10)
    file_size: Optional[int] = Field(None, ge=0)
    verification_status: VerificationStatus = VerificationStatus.PENDENTE
    notes: Optional[str] = None

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v):
        if not v.strip():
            raise ValueError("File name cannot be empty")
        return v.strip()

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        if not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class PaymentReceiptCreate(PaymentReceiptBase):
    pass


class PaymentReceiptUpdate(BaseModel):
    file_name: Optional[str] = Field(None, max_length=255)
    file_type: Optional[str] = Field(None, max_length=10)
    verification_status: Optional[VerificationStatus] = None
    notes: Optional[str] = None


class PaymentReceiptResponse(PaymentReceiptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    upload_date: datetime
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    uploaded_by: Optional[int] = None


# ==========================================
# BILLING AUDIT LOG SCHEMAS
# ==========================================


class BillingAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    action: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ==========================================
# LIST PARAMETERS AND RESPONSES
# ==========================================


class InvoiceListParams(BaseModel):
    contract_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    overdue_only: Optional[bool] = False
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class ReceiptListParams(BaseModel):
    invoice_id: Optional[int] = None
    verification_status: Optional[VerificationStatus] = None
    uploaded_by: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


class BillingScheduleListParams(BaseModel):
    contract_id: Optional[int] = None
    billing_cycle: Optional[BillingCycle] = None
    is_active: Optional[bool] = None
    next_billing_before: Optional[date] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)


# ==========================================
# RESPONSE CONTAINERS
# ==========================================


class InvoiceListResponse(BaseModel):
    invoices: List[ContractInvoiceResponse]
    total: int
    page: int
    size: int
    pages: int


class ReceiptListResponse(BaseModel):
    receipts: List[PaymentReceiptResponse]
    total: int
    page: int
    size: int
    pages: int


class BillingScheduleListResponse(BaseModel):
    schedules: List[ContractBillingScheduleResponse]
    total: int
    page: int
    size: int
    pages: int


# ==========================================
# DASHBOARD AND ANALYTICS SCHEMAS
# ==========================================


class BillingDashboardMetrics(BaseModel):
    total_pending_invoices: int = 0
    total_pending_amount: Decimal = Decimal("0.00")
    total_overdue_invoices: int = 0
    total_overdue_amount: Decimal = Decimal("0.00")
    total_paid_this_month: Decimal = Decimal("0.00")
    total_expected_this_month: Decimal = Decimal("0.00")
    collection_rate_percentage: Decimal = Decimal("0.00")
    average_payment_delay_days: Optional[int] = 0


class ContractBillingStatus(BaseModel):
    contract_id: int
    contract_number: str
    client_name: str
    monthly_value: Decimal
    pending_invoices: int = 0
    pending_amount: Decimal = Decimal("0.00")
    overdue_invoices: int = 0
    overdue_amount: Decimal = Decimal("0.00")
    last_payment_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    status: str


class BillingDashboardResponse(BaseModel):
    metrics: BillingDashboardMetrics
    recent_invoices: List[ContractInvoiceResponse]
    contracts_status: List[ContractBillingStatus]
    upcoming_billings: List[ContractBillingScheduleResponse]


# ==========================================
# BULK OPERATIONS SCHEMAS
# ==========================================


class BulkInvoiceGeneration(BaseModel):
    contract_ids: Optional[List[int]] = None
    billing_date: Optional[date] = None
    force_regenerate: bool = False


class BulkInvoiceGenerationResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    errors: List[str]
    generated_invoices: List[int]  # Invoice IDs


class BulkStatusUpdate(BaseModel):
    invoice_ids: List[int]
    new_status: InvoiceStatus
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class BulkStatusUpdateResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    errors: List[str]
    updated_invoices: List[int]