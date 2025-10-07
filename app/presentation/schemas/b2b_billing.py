"""
Schemas para sistema de cobrança B2B Pro Team Care
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

# ==========================================
# SUBSCRIPTION PLAN SCHEMAS
# ==========================================


class SubscriptionPlanBase(BaseModel):
    name: str = Field(..., description="Nome do plano")
    description: Optional[str] = Field(None, description="Descrição do plano")
    monthly_price: Decimal = Field(..., description="Preço mensal")
    features: Optional[dict] = Field(None, description="Features do plano")
    max_users: Optional[int] = Field(None, description="Máximo de usuários")
    max_establishments: Optional[int] = Field(
        None, description="Máximo de estabelecimentos"
    )
    is_active: bool = Field(default=True, description="Plano ativo")


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Schema para criação de plano de assinatura"""

    pass


class SubscriptionPlanUpdate(BaseModel):
    """Schema para atualização de plano de assinatura"""

    name: Optional[str] = Field(None, description="Nome do plano")
    description: Optional[str] = Field(None, description="Descrição do plano")
    monthly_price: Optional[Decimal] = Field(None, description="Preço mensal")
    features: Optional[dict] = Field(None, description="Features do plano")
    max_users: Optional[int] = Field(None, description="Máximo de usuários")
    max_establishments: Optional[int] = Field(
        None, description="Máximo de estabelecimentos"
    )
    is_active: Optional[bool] = Field(None, description="Plano ativo")


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==========================================
# COMPANY SUBSCRIPTION SCHEMAS
# ==========================================


class CompanySubscriptionCreate(BaseModel):
    company_id: int = Field(..., description="ID da empresa")
    plan_id: int = Field(..., description="ID do plano")
    start_date: date = Field(..., description="Data de início")
    billing_day: int = Field(default=1, description="Dia de cobrança", ge=1, le=31)
    payment_method: str = Field(default="manual", description="Método de pagamento")
    auto_renew: bool = Field(default=True, description="Renovação automática")


class CompanySubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = Field(None, description="ID do plano")
    billing_day: Optional[int] = Field(None, description="Dia de cobrança", ge=1, le=31)
    payment_method: Optional[str] = Field(None, description="Método de pagamento")
    auto_renew: Optional[bool] = Field(None, description="Renovação automática")
    status: Optional[str] = Field(None, description="Status da assinatura")


class CompanySubscriptionResponse(BaseModel):
    id: int
    company_id: int
    plan_id: int
    status: str
    start_date: date
    end_date: Optional[date] = None
    billing_day: int
    payment_method: str
    pagbank_subscription_id: Optional[str] = None
    auto_renew: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relacionamentos
    plan: Optional[SubscriptionPlanResponse] = None

    class Config:
        from_attributes = True


class CompanySubscriptionsBatchRequest(BaseModel):
    """Schema para requisição batch de subscriptions"""

    company_ids: List[int] = Field(..., description="IDs das empresas")


class CompanySubscriptionsBatchResponse(BaseModel):
    """Schema para resposta batch de subscriptions"""

    subscriptions: List[Optional[CompanySubscriptionResponse]] = Field(
        ..., description="Lista de subscriptions (None para empresas sem assinatura)"
    )


# ==========================================
# PRO TEAM CARE INVOICE SCHEMAS
# ==========================================


class CreateProTeamCareInvoiceRequest(BaseModel):
    company_id: int = Field(..., description="ID da empresa")
    subscription_id: int = Field(..., description="ID da assinatura")
    billing_period_start: date = Field(..., description="Início do período")
    billing_period_end: date = Field(..., description="Fim do período")
    due_date: date = Field(..., description="Data de vencimento")
    amount: Decimal = Field(..., description="Valor da fatura")
    notes: Optional[str] = Field(None, description="Observações")


class ProTeamCareInvoiceResponse(BaseModel):
    id: int
    company_id: int
    subscription_id: int
    invoice_number: str
    amount: Decimal
    billing_period_start: date
    billing_period_end: date
    due_date: date
    status: str
    payment_method: str
    paid_at: Optional[datetime] = None
    pagbank_checkout_url: Optional[str] = None
    pagbank_session_id: Optional[str] = None
    pagbank_transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateCheckoutSessionRequest(BaseModel):
    invoice_id: int = Field(..., description="ID da fatura Pro Team Care")


class CheckoutSessionResponse(BaseModel):
    success: bool
    invoice_id: int
    checkout_url: str
    session_id: str
    expires_at: str
    qr_code: Optional[str] = None
    transaction_id: Optional[int] = None


# ==========================================
# DASHBOARD SCHEMAS
# ==========================================


class B2BBillingMetrics(BaseModel):
    total_companies: int
    active_subscriptions: int
    monthly_revenue: Decimal
    pending_invoices: int
    overdue_invoices: int
    paid_invoices_this_month: int
    total_revenue_this_month: Decimal


class CompanyBillingStatus(BaseModel):
    company_id: int
    company_name: str
    plan_name: str
    monthly_amount: Decimal
    last_payment: Optional[date] = None
    next_billing: Optional[date] = None
    status: str
    overdue_amount: Decimal
    payment_method: str


class B2BDashboardResponse(BaseModel):
    metrics: B2BBillingMetrics
    companies_status: List[CompanyBillingStatus]
    recent_payments: List[ProTeamCareInvoiceResponse]
    plan_distribution: dict


# ==========================================
# BULK OPERATION SCHEMAS
# ==========================================


class BulkInvoiceGenerationRequest(BaseModel):
    target_month: int = Field(..., description="Mês alvo", ge=1, le=12)
    target_year: int = Field(..., description="Ano alvo")
    company_ids: Optional[List[int]] = Field(
        None, description="IDs específicas das empresas"
    )
    send_emails: bool = Field(
        default=False, description="Enviar emails automaticamente"
    )


class BulkInvoiceGenerationResponse(BaseModel):
    success: bool
    total_companies: int
    invoices_created: int
    invoices_failed: int
    total_amount: Decimal
    errors: List[str] = []


# ==========================================
# PAYMENT TRACKING SCHEMAS
# ==========================================


class PaymentConfirmationRequest(BaseModel):
    invoice_id: int = Field(..., description="ID da fatura")
    payment_method: str = Field(..., description="Método de pagamento")
    payment_date: date = Field(..., description="Data do pagamento")
    transaction_reference: Optional[str] = Field(
        None, description="Referência da transação"
    )
    notes: Optional[str] = Field(None, description="Observações")


class PaymentStatusUpdate(BaseModel):
    invoice_id: int
    old_status: str
    new_status: str
    payment_date: Optional[date] = None
    updated_at: datetime
