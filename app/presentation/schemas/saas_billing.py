from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# ==========================================
# ENUMS
# ==========================================


class SubscriptionStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"
    suspended = "suspended"
    expired = "expired"


class SaasPaymentMethod(str, Enum):
    manual = "manual"
    recurrent = "recurrent"


class SaasInvoiceStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


# ==========================================
# SUBSCRIPTION SCHEMAS
# ==========================================


class CompanySubscriptionBase(BaseModel):
    company_id: int
    plan_id: int
    billing_day: int = Field(default=1, ge=1, le=31)
    payment_method: SaasPaymentMethod = SaasPaymentMethod.manual
    auto_renew: bool = True


class CompanySubscriptionCreate(CompanySubscriptionBase):
    # Campos opcionais para envio automático de email de ativação
    send_activation_email: bool = Field(
        default=True, description="Enviar email de ativação automaticamente"
    )
    recipient_email: Optional[str] = Field(
        None,
        description="Email do responsável (se não informado, busca emails cadastrados)",
    )
    recipient_name: Optional[str] = Field(None, description="Nome do responsável")


class CompanySubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    status: Optional[SubscriptionStatus] = None
    billing_day: Optional[int] = Field(None, ge=1, le=31)
    payment_method: Optional[SaasPaymentMethod] = None
    end_date: Optional[date] = None
    auto_renew: Optional[bool] = None


class CompanySubscriptionResponse(CompanySubscriptionBase):
    id: int
    status: SubscriptionStatus
    start_date: date
    end_date: Optional[date]
    pagbank_subscription_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Related data
    company_name: Optional[str] = None
    plan_name: Optional[str] = None
    plan_monthly_price: Optional[Decimal] = None

    class Config:
        from_attributes = True

    @validator("company_name", pre=True, always=True)
    def extract_company_name(cls, v, values):
        return (
            getattr(values.get("company"), "name", None)
            if hasattr(values.get("company", {}), "name")
            else v
        )

    @validator("plan_name", pre=True, always=True)
    def extract_plan_name(cls, v, values):
        return (
            getattr(values.get("plan"), "name", None)
            if hasattr(values.get("plan", {}), "name")
            else v
        )

    @validator("plan_monthly_price", pre=True, always=True)
    def extract_plan_price(cls, v, values):
        return (
            getattr(values.get("plan"), "monthly_price", None)
            if hasattr(values.get("plan", {}), "monthly_price")
            else v
        )


class SubscriptionListParams(BaseModel):
    company_id: Optional[int] = None
    plan_id: Optional[int] = None
    status: Optional[SubscriptionStatus] = None
    payment_method: Optional[SaasPaymentMethod] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=100)


class SubscriptionListResponse(BaseModel):
    subscriptions: List[CompanySubscriptionResponse]
    total: int
    page: int
    size: int
    pages: int


# ==========================================
# INVOICE SCHEMAS
# ==========================================


class SaasInvoiceBase(BaseModel):
    company_id: int
    subscription_id: int
    amount: Decimal = Field(..., gt=0)
    billing_period_start: date
    billing_period_end: date
    due_date: date
    payment_method: SaasPaymentMethod = SaasPaymentMethod.manual
    notes: Optional[str] = None


class SaasInvoiceCreate(SaasInvoiceBase):
    pass


class SaasInvoiceUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None
    status: Optional[SaasInvoiceStatus] = None
    payment_method: Optional[SaasPaymentMethod] = None
    pagbank_checkout_url: Optional[str] = None
    pagbank_session_id: Optional[str] = None
    pagbank_transaction_id: Optional[str] = None
    notes: Optional[str] = None


class SaasInvoiceResponse(SaasInvoiceBase):
    id: int
    invoice_number: str
    status: SaasInvoiceStatus
    paid_at: Optional[datetime]
    pagbank_checkout_url: Optional[str]
    pagbank_session_id: Optional[str]
    pagbank_transaction_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SaasInvoiceDetailed(SaasInvoiceResponse):
    # Related data
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    company_tax_id: Optional[str] = None
    subscription_plan_name: Optional[str] = None
    subscription_billing_day: Optional[int] = None

    @validator("company_name", pre=True, always=True)
    def extract_company_name(cls, v, values):
        return (
            getattr(values.get("company"), "name", None)
            if hasattr(values.get("company", {}), "name")
            else v
        )

    @validator("company_email", pre=True, always=True)
    def extract_company_email(cls, v, values):
        return (
            getattr(values.get("company"), "email", None)
            if hasattr(values.get("company", {}), "email")
            else v
        )

    @validator("company_tax_id", pre=True, always=True)
    def extract_company_tax_id(cls, v, values):
        return (
            getattr(values.get("company"), "tax_id", None)
            if hasattr(values.get("company", {}), "tax_id")
            else v
        )

    @validator("subscription_plan_name", pre=True, always=True)
    def extract_subscription_plan_name(cls, v, values):
        subscription = values.get("subscription")
        if (
            subscription
            and hasattr(subscription, "plan")
            and hasattr(subscription.plan, "name")
        ):
            return subscription.plan.name
        return v

    @validator("subscription_billing_day", pre=True, always=True)
    def extract_subscription_billing_day(cls, v, values):
        return (
            getattr(values.get("subscription"), "billing_day", None)
            if hasattr(values.get("subscription", {}), "billing_day")
            else v
        )


class SaasInvoiceListParams(BaseModel):
    company_id: Optional[int] = None
    subscription_id: Optional[int] = None
    status: Optional[SaasInvoiceStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    overdue_only: bool = False
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=100)


class SaasInvoiceListResponse(BaseModel):
    invoices: List[SaasInvoiceResponse]
    total: int
    page: int
    size: int
    pages: int


# ==========================================
# PAYMENT SCHEMAS
# ==========================================


class PaymentLinkRequest(BaseModel):
    notification_url: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentLinkResponse(BaseModel):
    success: bool
    invoice_id: int
    checkout_url: str
    session_id: str
    message: Optional[str] = None


class ManualPaymentRequest(BaseModel):
    payment_method: str = Field(..., description="Payment method used")
    payment_reference: Optional[str] = Field(
        None, description="Payment reference/transaction ID"
    )
    notes: Optional[str] = Field(None, description="Additional notes about the payment")


class ManualPaymentResponse(BaseModel):
    success: bool
    invoice_id: int
    message: str


# ==========================================
# RECURRENT BILLING SCHEMAS
# ==========================================


class CustomerData(BaseModel):
    name: str
    email: str
    document: str
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None


class RecurrentBillingSetupRequest(BaseModel):
    customer_data: CustomerData


class RecurrentBillingSetupResponse(BaseModel):
    success: bool
    subscription_id: int
    pagbank_subscription_id: str
    pagbank_customer_id: str
    message: Optional[str] = None


class SubscriptionCancelRequest(BaseModel):
    cancel_pagbank: bool = True
    reason: Optional[str] = None


class SubscriptionCancelResponse(BaseModel):
    success: bool
    subscription_id: int
    message: str


# ==========================================
# AUTOMATIC BILLING SCHEMAS
# ==========================================


class AutomaticSaasBillingRequest(BaseModel):
    billing_date: Optional[date] = None
    force_regenerate: bool = False


class AutomaticSaasBillingResponse(BaseModel):
    total_subscriptions_processed: int
    successful_invoices: int
    failed_invoices: int
    generated_invoice_ids: List[int]
    errors: List[str]
    billing_date: str


# ==========================================
# DASHBOARD SCHEMAS
# ==========================================


class SaasBillingMetrics(BaseModel):
    total_active_subscriptions: int
    total_establishments: int
    total_pending_invoices: int
    total_pending_amount: Decimal
    total_overdue_invoices: int
    total_overdue_amount: Decimal
    total_paid_this_month: Decimal
    total_expected_this_month: Decimal
    collection_rate_percentage: Decimal
    monthly_recurring_revenue: Decimal
    average_revenue_per_user: Decimal


class SaasBillingDashboardResponse(BaseModel):
    metrics: SaasBillingMetrics
    last_updated: date


class MonthlyRevenueReport(BaseModel):
    period: str
    total_billed: Decimal
    total_paid: Decimal
    total_pending: Decimal
    total_overdue: Decimal
    collection_rate: Decimal
    invoices_count: int


# ==========================================
# PLAN SCHEMAS (for reference)
# ==========================================


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    monthly_price: Decimal
    features: Optional[Dict[str, Any]]
    max_users: Optional[int]
    max_establishments: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
