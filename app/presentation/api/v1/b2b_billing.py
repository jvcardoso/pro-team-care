"""
Endpoints API para sistema de cobrança B2B Pro Team Care
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.b2b_billing_repository import B2BBillingRepository
from app.infrastructure.services.b2b_billing_service import B2BBillingService
from app.infrastructure.services.pagbank_service import PagBankService
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.b2b_billing import (
    B2BDashboardResponse,
    BulkInvoiceGenerationRequest,
    BulkInvoiceGenerationResponse,
    CheckoutSessionResponse,
    CompanySubscriptionCreate,
    CompanySubscriptionResponse,
    CompanySubscriptionsBatchRequest,
    CompanySubscriptionsBatchResponse,
    CompanySubscriptionUpdate,
    CreateCheckoutSessionRequest,
    CreateProTeamCareInvoiceRequest,
    PaymentConfirmationRequest,
    ProTeamCareInvoiceResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)

router = APIRouter()


def get_b2b_billing_service(db: AsyncSession = Depends(get_db)) -> B2BBillingService:
    """Dependency para obter o serviço B2B"""
    repository = B2BBillingRepository(db)
    pagbank_service = PagBankService()
    return B2BBillingService(repository, pagbank_service)


# ==========================================
# SUBSCRIPTION PLAN ENDPOINTS
# ==========================================


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
@require_permission("billing_admin", context_type="system")
async def list_subscription_plans(
    active_only: bool = Query(True, description="Apenas planos ativos"),
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Listar planos de assinatura disponíveis"""
    plans = await service.repository.get_subscription_plans(active_only=active_only)
    return plans


@router.post("/plans", response_model=SubscriptionPlanResponse)
@require_permission("billing_admin", context_type="system")
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Criar novo plano de assinatura"""
    try:
        plan = await service.create_subscription_plan(plan_data)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
@require_permission("billing_admin", context_type="system")
async def get_subscription_plan(
    plan_id: int,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar plano de assinatura por ID"""
    plan = await service.repository.get_subscription_plan_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado"
        )
    return plan


@router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
@require_permission("billing_admin", context_type="system")
async def update_subscription_plan(
    plan_id: int,
    plan_data: SubscriptionPlanUpdate,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Atualizar plano de assinatura"""
    try:
        plan = await service.update_subscription_plan(plan_id, plan_data)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado"
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/plans/{plan_id}")
@require_permission("billing_admin", context_type="system")
async def delete_subscription_plan(
    plan_id: int,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Desativar plano de assinatura"""
    try:
        result = await service.delete_subscription_plan(plan_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# COMPANY SUBSCRIPTION ENDPOINTS
# ==========================================


@router.post("/subscriptions", response_model=CompanySubscriptionResponse)
@require_permission("billing_admin", context_type="system")
async def create_company_subscription(
    subscription_data: CompanySubscriptionCreate,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Criar nova assinatura para empresa"""
    try:
        subscription = await service.create_company_subscription(subscription_data)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/subscriptions/company/{company_id}", response_model=CompanySubscriptionResponse
)
@require_permission("billing_view", context_type="system")
async def get_company_subscription(
    company_id: int,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar assinatura de uma empresa"""
    subscription = await service.repository.get_company_subscription(company_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assinatura não encontrada"
        )
    return subscription


@router.post("/subscriptions/batch", response_model=CompanySubscriptionsBatchResponse)
@require_permission("billing_view", context_type="system")
async def get_company_subscriptions_batch(
    request: CompanySubscriptionsBatchRequest,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar assinaturas de múltiplas empresas (bulk operation)

    Retorna uma lista de subscriptions na mesma ordem dos company_ids.
    Empresas sem assinatura ativa retornam None na posição correspondente.

    Exemplo:
    - Request: {"company_ids": [1, 2, 3]}
    - Response: {"subscriptions": [<Subscription>, None, <Subscription>]}
      (empresa 2 não possui assinatura ativa)
    """
    subscriptions = await service.repository.get_company_subscriptions_batch(
        request.company_ids
    )
    return CompanySubscriptionsBatchResponse(subscriptions=subscriptions)


@router.put(
    "/subscriptions/{subscription_id}", response_model=CompanySubscriptionResponse
)
@require_permission("billing_manage", context_type="system")
async def update_company_subscription(
    subscription_id: int,
    update_data: CompanySubscriptionUpdate,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Atualizar assinatura da empresa"""
    try:
        subscription = await service.repository.update_company_subscription(
            subscription_id, update_data.model_dump(exclude_unset=True)
        )
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assinatura não encontrada",
            )
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        import structlog

        logger = structlog.get_logger()
        logger.error(
            "Erro ao atualizar assinatura",
            subscription_id=subscription_id,
            update_data=update_data.model_dump(exclude_unset=True),
            error=str(e),
            error_type=type(e).__name__,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao atualizar assinatura: {str(e)}",
        )


# ==========================================
# INVOICE ENDPOINTS
# ==========================================


@router.post("/invoices", response_model=ProTeamCareInvoiceResponse)
@require_permission("billing_admin", context_type="system")
async def create_manual_invoice(
    invoice_request: CreateProTeamCareInvoiceRequest,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Criar fatura manual para empresa"""
    try:
        invoice = await service.create_manual_invoice(invoice_request)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/invoices/{invoice_id}", response_model=ProTeamCareInvoiceResponse)
@require_permission("billing_view", context_type="system")
async def get_invoice(
    invoice_id: int,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar fatura por ID"""
    invoice = await service.repository.get_proteamcare_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fatura não encontrada"
        )
    return invoice


@router.get(
    "/invoices/company/{company_id}", response_model=List[ProTeamCareInvoiceResponse]
)
@require_permission("billing_view", context_type="system")
async def list_company_invoices(
    company_id: int,
    status_filter: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, description="Máximo de faturas", ge=1, le=200),
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Listar faturas de uma empresa"""
    invoices = await service.repository.get_company_invoices(
        company_id=company_id, status=status_filter, limit=limit
    )
    return invoices


@router.get(
    "/invoices/status/{status}", response_model=List[ProTeamCareInvoiceResponse]
)
@require_permission("billing_view", context_type="system")
async def list_invoices_by_status(
    status: str,
    limit: int = Query(100, description="Máximo de faturas", ge=1, le=200),
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Listar faturas por status"""
    invoices = await service.repository.get_invoices_by_status(status, limit)
    return invoices


@router.get("/invoices/overdue/list", response_model=List[ProTeamCareInvoiceResponse])
@require_permission("billing_view", context_type="system")
async def list_overdue_invoices(
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Listar faturas vencidas"""
    invoices = await service.get_overdue_invoices()
    return invoices


# ==========================================
# PAYMENT ENDPOINTS
# ==========================================


@router.post("/invoices/{invoice_id}/checkout", response_model=CheckoutSessionResponse)
@require_permission("billing_admin", context_type="system")
async def create_checkout_session(
    invoice_id: int,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Criar sessão de checkout para fatura"""
    try:
        checkout_response = await service.create_checkout_session(invoice_id)
        return checkout_response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invoices/{invoice_id}/mark-paid")
@require_permission("billing_admin", context_type="system")
async def mark_invoice_as_paid(
    invoice_id: int,
    payment_data: PaymentConfirmationRequest,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Marcar fatura como paga manualmente"""
    try:
        invoice = await service.mark_invoice_as_paid(
            invoice_id=invoice_id,
            payment_method=payment_data.payment_method,
            payment_date=payment_data.payment_date,
            transaction_reference=payment_data.transaction_reference,
        )
        return {
            "success": True,
            "invoice_id": invoice_id,
            "status": invoice.status,
            "paid_at": invoice.paid_at,
            "message": "Fatura marcada como paga com sucesso",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# BULK OPERATIONS
# ==========================================


@router.post("/invoices/bulk-generate", response_model=BulkInvoiceGenerationResponse)
@require_permission("billing_admin", context_type="system")
async def bulk_generate_invoices(
    request: BulkInvoiceGenerationRequest,
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Gerar faturas em lote para um mês específico"""
    try:
        result = await service.generate_monthly_invoices(
            target_month=request.target_month,
            target_year=request.target_year,
            company_ids=request.company_ids,
        )
        return BulkInvoiceGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na geração de faturas: {str(e)}",
        )


# ==========================================
# DASHBOARD ENDPOINTS
# ==========================================


@router.get("/dashboard")
@require_permission("billing_view", context_type="system")
async def get_b2b_dashboard(
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar dados do dashboard B2B"""
    try:
        dashboard_data = await service.get_dashboard_data()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados do dashboard: {str(e)}",
        )


# ==========================================
# WEBHOOK ENDPOINTS
# ==========================================


@router.post("/webhook/pagbank")
async def pagbank_webhook(
    webhook_data: dict,
    service: B2BBillingService = Depends(get_b2b_billing_service),
):
    """Webhook do PagBank para pagamentos B2B"""
    try:
        processed = await service.process_pagbank_webhook(webhook_data)
        return {
            "success": processed,
            "message": (
                "Webhook processado com sucesso"
                if processed
                else "Erro no processamento"
            ),
        }
    except Exception as e:
        # Log do erro mas retornar sucesso para evitar reenvios
        print(f"Erro no webhook PagBank B2B: {str(e)}")
        return {"success": False, "message": "Erro interno"}


# ==========================================
# UTILITY ENDPOINTS
# ==========================================


@router.get("/companies-for-billing")
@require_permission("billing_view", context_type="system")
async def get_companies_for_billing(
    billing_day: int = Query(..., description="Dia de cobrança", ge=1, le=31),
    service: B2BBillingService = Depends(get_b2b_billing_service),
    current_user: User = Depends(get_current_user),
):
    """Buscar empresas para faturamento em um dia específico"""
    companies = await service.repository.get_companies_for_billing(billing_day)
    return {
        "billing_day": billing_day,
        "total_companies": len(companies),
        "companies": [
            {
                "company_id": comp.company_id,
                "company_name": (
                    comp.company.people.name
                    if comp.company.people
                    else f"Empresa {comp.company_id}"
                ),
                "plan_name": comp.plan.name,
                "monthly_amount": comp.plan.monthly_price,
            }
            for comp in companies
        ],
    }


# DEBUG ENDPOINT - TEMPORÁRIO
@router.get("/debug/company/{company_id}/subscription")
async def debug_company_subscription(
    company_id: int, service: B2BBillingService = Depends(get_b2b_billing_service)
):
    """Debug: Verificar estrutura da subscription"""
    try:
        subscription = await service.repository.get_company_subscription(company_id)

        if subscription:
            return {
                "found": True,
                "subscription": {
                    "id": subscription.id,
                    "company_id": subscription.company_id,
                    "plan_id": subscription.plan_id,
                    "status": subscription.status,
                    "billing_day": subscription.billing_day,
                    "payment_method": subscription.payment_method,
                    "auto_renew": subscription.auto_renew,
                    "plan_info": (
                        {
                            "id": subscription.plan.id if subscription.plan else None,
                            "name": (
                                subscription.plan.name if subscription.plan else None
                            ),
                            "monthly_price": (
                                subscription.plan.monthly_price
                                if subscription.plan
                                else None
                            ),
                        }
                        if subscription.plan
                        else None
                    ),
                },
            }
        else:
            return {"found": False, "message": "Subscription not found"}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


# DEBUG ENDPOINT - VERIFICAR FATURA
@router.get("/debug/invoice/{invoice_id}")
async def debug_invoice(
    invoice_id: int, service: B2BBillingService = Depends(get_b2b_billing_service)
):
    """Debug: Verificar estrutura da fatura"""
    try:
        invoice = await service.repository.get_proteamcare_invoice_by_id(invoice_id)

        if invoice:
            return {
                "found": True,
                "invoice": {
                    "id": invoice.id,
                    "company_id": invoice.company_id,
                    "amount": float(invoice.amount),
                    "status": invoice.status,
                    "invoice_number": invoice.invoice_number,
                    "company_info": (
                        {
                            "id": invoice.company.id if invoice.company else None,
                            "people_name": (
                                invoice.company.people.name
                                if invoice.company and invoice.company.people
                                else None
                            ),
                            "people_tax_id": (
                                invoice.company.people.tax_id
                                if invoice.company and invoice.company.people
                                else None
                            ),
                        }
                        if invoice.company
                        else None
                    ),
                },
            }
        else:
            return {"found": False, "message": "Invoice not found"}
    except Exception as e:
        import traceback

        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }


# DEBUG ENDPOINT - TESTAR CHECKOUT
@router.post("/debug/invoice/{invoice_id}/test-checkout")
async def debug_test_checkout(
    invoice_id: int, service: B2BBillingService = Depends(get_b2b_billing_service)
):
    """Debug: Testar criação de checkout sem autenticação"""
    try:
        result = await service.create_checkout_session(invoice_id)
        return {"success": True, "result": result}
    except Exception as e:
        import traceback

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }
