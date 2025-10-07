from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.saas_billing_repository import (
    SaasBillingRepository,
)
from app.infrastructure.services.saas_billing_service import SaasBillingService
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.pagbank import WebhookRequest, WebhookResponse
from app.presentation.schemas.saas_billing import (  # Subscription Schemas; Invoice Schemas; Dashboard Schemas; Payment Schemas; Billing Management
    AutomaticSaasBillingRequest,
    AutomaticSaasBillingResponse,
    CompanySubscriptionCreate,
    CompanySubscriptionResponse,
    CompanySubscriptionUpdate,
    ManualPaymentRequest,
    ManualPaymentResponse,
    MonthlyRevenueReport,
    PaymentLinkRequest,
    PaymentLinkResponse,
    RecurrentBillingSetupRequest,
    RecurrentBillingSetupResponse,
    SaasBillingDashboardResponse,
    SaasBillingMetrics,
    SaasInvoiceCreate,
    SaasInvoiceDetailed,
    SaasInvoiceListParams,
    SaasInvoiceListResponse,
    SaasInvoiceResponse,
    SaasInvoiceUpdate,
    SubscriptionCancelRequest,
    SubscriptionCancelResponse,
    SubscriptionListParams,
    SubscriptionListResponse,
)

router = APIRouter()


# ==========================================
# SUBSCRIPTION ENDPOINTS
# ==========================================


@router.get("/subscriptions", response_model=SubscriptionListResponse)
@require_permission("saas_billing_view", context_type="system")
async def list_subscriptions(
    params: SubscriptionListParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List company subscriptions with filtering and pagination"""
    repository = SaasBillingRepository(db)

    result = await repository.list_subscriptions(
        company_id=params.company_id,
        plan_id=params.plan_id,
        status=params.status,
        payment_method=params.payment_method,
        page=params.page,
        size=params.size,
    )

    return SubscriptionListResponse(**result)


@router.get(
    "/subscriptions/{subscription_id}", response_model=CompanySubscriptionResponse
)
@require_permission("saas_billing_view", context_type="system")
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get subscription by ID"""
    repository = SaasBillingRepository(db)

    subscription = await repository.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    return CompanySubscriptionResponse.from_orm(subscription)


@router.get(
    "/subscriptions/company/{company_id}", response_model=CompanySubscriptionResponse
)
@require_permission("saas_billing_view", context_type="company")
async def get_subscription_by_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get active subscription for a company"""
    repository = SaasBillingRepository(db)

    subscription = await repository.get_subscription_by_company(company_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active subscription found for company {company_id}",
        )

    return CompanySubscriptionResponse.from_orm(subscription)


@router.post("/subscriptions", response_model=CompanySubscriptionResponse)
@require_permission("saas_billing_create", context_type="system")
async def create_subscription(
    subscription_data: CompanySubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new company subscription

    🔥 NOVO: Envia email de ativação automaticamente após criar assinatura!

    - Se `send_activation_email=true` (padrão), envia email para o cliente
    - Se `recipient_email` fornecido, usa ele; senão busca emails cadastrados
    - Email contém link para aceitar contrato e criar credenciais de acesso
    """
    service = SaasBillingService(db)

    subscription = await service.create_subscription(
        company_id=subscription_data.company_id,
        plan_id=subscription_data.plan_id,
        billing_day=subscription_data.billing_day,
        payment_method=subscription_data.payment_method,
        auto_renew=subscription_data.auto_renew,
        send_activation_email=subscription_data.send_activation_email,
        recipient_email=subscription_data.recipient_email,
        recipient_name=subscription_data.recipient_name,
    )

    return CompanySubscriptionResponse.from_orm(subscription)


@router.put(
    "/subscriptions/{subscription_id}", response_model=CompanySubscriptionResponse
)
@require_permission("saas_billing_update", context_type="system")
async def update_subscription(
    subscription_id: int,
    update_data: CompanySubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update subscription"""
    repository = SaasBillingRepository(db)

    subscription = await repository.update_subscription(
        subscription_id, update_data.dict(exclude_unset=True)
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    return CompanySubscriptionResponse.from_orm(subscription)


@router.post(
    "/subscriptions/{subscription_id}/cancel", response_model=SubscriptionCancelResponse
)
@require_permission("saas_billing_cancel", context_type="system")
async def cancel_subscription(
    subscription_id: int,
    cancel_data: SubscriptionCancelRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a subscription"""
    service = SaasBillingService(db)

    try:
        subscription = await service.cancel_subscription(
            subscription_id, cancel_pagbank=cancel_data.cancel_pagbank
        )

        return SubscriptionCancelResponse(
            success=True,
            subscription_id=subscription_id,
            message="Subscription cancelled successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# INVOICE ENDPOINTS
# ==========================================


@router.get("/invoices", response_model=SaasInvoiceListResponse)
@require_permission("saas_billing_view", context_type="system")
async def list_invoices(
    params: SaasInvoiceListParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List SaaS invoices with filtering and pagination"""
    repository = SaasBillingRepository(db)

    result = await repository.list_saas_invoices(
        company_id=params.company_id,
        subscription_id=params.subscription_id,
        status=params.status,
        start_date=params.start_date,
        end_date=params.end_date,
        overdue_only=params.overdue_only,
        page=params.page,
        size=params.size,
    )

    return SaasInvoiceListResponse(**result)


@router.get("/invoices/{invoice_id}", response_model=SaasInvoiceDetailed)
@require_permission("saas_billing_view", context_type="system")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get SaaS invoice by ID with detailed information"""
    repository = SaasBillingRepository(db)

    invoice = await repository.get_saas_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return SaasInvoiceDetailed.from_orm(invoice)


@router.post("/invoices", response_model=SaasInvoiceResponse)
@require_permission("saas_billing_create", context_type="system")
async def create_invoice(
    invoice_data: SaasInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new SaaS invoice"""
    repository = SaasBillingRepository(db)

    invoice = await repository.create_saas_invoice(invoice_data.dict())

    return SaasInvoiceResponse.from_orm(invoice)


@router.put("/invoices/{invoice_id}", response_model=SaasInvoiceResponse)
@require_permission("saas_billing_update", context_type="system")
async def update_invoice(
    invoice_id: int,
    update_data: SaasInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update SaaS invoice"""
    repository = SaasBillingRepository(db)

    invoice = await repository.update_saas_invoice(
        invoice_id, update_data.dict(exclude_unset=True)
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    return SaasInvoiceResponse.from_orm(invoice)


# ==========================================
# PAYMENT ENDPOINTS
# ==========================================


@router.post("/invoices/{invoice_id}/payment-link", response_model=PaymentLinkResponse)
@require_permission("saas_billing_payment", context_type="system")
async def generate_payment_link(
    invoice_id: int,
    payment_data: PaymentLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate payment link for an invoice"""
    service = SaasBillingService(db)

    try:
        result = await service.generate_payment_link(invoice_id)

        return PaymentLinkResponse(
            success=result["success"],
            invoice_id=result["invoice_id"],
            checkout_url=result["checkout_url"],
            session_id=result["session_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/invoices/{invoice_id}/manual-payment", response_model=ManualPaymentResponse
)
@require_permission("saas_billing_payment", context_type="system")
async def process_manual_payment(
    invoice_id: int,
    payment_data: ManualPaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process manual payment for an invoice"""
    service = SaasBillingService(db)

    try:
        invoice = await service.process_manual_payment(
            invoice_id,
            payment_data.payment_method,
            payment_data.payment_reference,
            payment_data.notes,
        )

        return ManualPaymentResponse(
            success=True,
            invoice_id=invoice_id,
            message="Payment processed successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# RECURRENT BILLING ENDPOINTS
# ==========================================


@router.post(
    "/subscriptions/{subscription_id}/setup-recurrent",
    response_model=RecurrentBillingSetupResponse,
)
@require_permission("saas_billing_recurrent", context_type="system")
async def setup_recurrent_billing(
    subscription_id: int,
    setup_data: RecurrentBillingSetupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Setup recurrent billing for a subscription"""
    service = SaasBillingService(db)

    try:
        result = await service.setup_recurrent_billing(
            subscription_id, setup_data.customer_data.dict()
        )

        return RecurrentBillingSetupResponse(
            success=result["success"],
            subscription_id=result["subscription_id"],
            pagbank_subscription_id=result["pagbank_subscription_id"],
            pagbank_customer_id=result["pagbank_customer_id"],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# AUTOMATIC BILLING ENDPOINTS
# ==========================================


@router.post("/billing/run-automatic", response_model=AutomaticSaasBillingResponse)
@require_permission("saas_billing_automatic", context_type="system")
async def run_automatic_billing(
    billing_data: AutomaticSaasBillingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run automatic SaaS billing process"""
    service = SaasBillingService(db)

    try:
        result = await service.run_automatic_saas_billing(
            billing_date=billing_data.billing_date,
            force_regenerate=billing_data.force_regenerate,
        )

        return AutomaticSaasBillingResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automatic billing failed: {str(e)}",
        )


# ==========================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# ==========================================


@router.get("/dashboard", response_model=SaasBillingDashboardResponse)
@require_permission("saas_billing_dashboard", context_type="system")
async def get_billing_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """Get SaaS billing dashboard metrics"""
    service = SaasBillingService(db)

    metrics = await service.get_saas_dashboard_metrics()

    return SaasBillingDashboardResponse(
        metrics=SaasBillingMetrics(**metrics), last_updated=date.today()
    )


@router.get("/reports/monthly-revenue", response_model=MonthlyRevenueReport)
@require_permission("saas_billing_reports", context_type="system")
async def get_monthly_revenue_report(
    year: int = Query(..., description="Year for the report"),
    month: int = Query(..., ge=1, le=12, description="Month for the report (1-12)"),
    db: AsyncSession = Depends(get_db),
):
    """Get monthly revenue report"""
    service = SaasBillingService(db)

    report = await service.get_monthly_revenue_report(year, month)

    return MonthlyRevenueReport(**report)


# ==========================================
# WEBHOOK ENDPOINTS
# ==========================================


@router.post("/webhooks/pagbank", response_model=WebhookResponse)
async def pagbank_webhook(
    webhook_data: WebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process PagBank webhook for SaaS payments"""
    service = SaasBillingService(db)

    try:
        result = await service.process_pagbank_webhook(webhook_data.dict())

        return WebhookResponse(
            success=result["success"],
            message=result.get("error", "Webhook processed successfully"),
        )
    except Exception as e:
        return WebhookResponse(
            success=False, message=f"Webhook processing failed: {str(e)}"
        )
