"""
Serviço para sistema de cobrança B2B Pro Team Care
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from app.infrastructure.orm.models import CompanySubscription, ProTeamCareInvoice
from app.infrastructure.repositories.b2b_billing_repository import B2BBillingRepository
from app.infrastructure.services.pagbank_service import PagBankService
from app.presentation.schemas.b2b_billing import (
    CheckoutSessionResponse,
    CompanySubscriptionCreate,
    CreateProTeamCareInvoiceRequest,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
)


class B2BBillingService:
    """Serviço para operações de cobrança B2B"""

    def __init__(
        self, repository: B2BBillingRepository, pagbank_service: PagBankService
    ):
        self.repository = repository
        self.pagbank_service = pagbank_service

    # ==========================================
    # SUBSCRIPTION PLAN MANAGEMENT
    # ==========================================

    async def create_subscription_plan(self, plan_data: SubscriptionPlanCreate):
        """Criar novo plano de assinatura"""
        # Verificar se já existe plano com mesmo nome
        existing_plans = await self.repository.get_subscription_plans(active_only=False)
        if any(plan.name.lower() == plan_data.name.lower() for plan in existing_plans):
            raise ValueError("Já existe um plano com este nome")

        plan_dict = plan_data.model_dump()
        plan_dict["created_at"] = datetime.now()

        return await self.repository.create_subscription_plan(plan_dict)

    async def update_subscription_plan(
        self, plan_id: int, plan_data: SubscriptionPlanUpdate
    ):
        """Atualizar plano de assinatura"""
        plan = await self.repository.get_subscription_plan_by_id(plan_id)
        if not plan:
            raise ValueError("Plano não encontrado")

        # Verificar se nome já existe (exceto para o próprio plano)
        if plan_data.name:
            existing_plans = await self.repository.get_subscription_plans(
                active_only=False
            )
            if any(
                p.name.lower() == plan_data.name.lower() and p.id != plan_id
                for p in existing_plans
            ):
                raise ValueError("Já existe um plano com este nome")

        update_dict = plan_data.model_dump(exclude_unset=True)
        return await self.repository.update_subscription_plan(plan_id, update_dict)

    async def delete_subscription_plan(self, plan_id: int):
        """Desativar plano de assinatura"""
        plan = await self.repository.get_subscription_plan_by_id(plan_id)
        if not plan:
            raise ValueError("Plano não encontrado")

        # Verificar se há assinaturas ativas usando este plano
        # (implementar se necessário)

        success = await self.repository.delete_subscription_plan(plan_id)
        if not success:
            raise ValueError("Erro ao desativar plano")

        return {"success": True, "message": "Plano desativado com sucesso"}

    # ==========================================
    # SUBSCRIPTION MANAGEMENT
    # ==========================================

    async def create_company_subscription(
        self, subscription_data: CompanySubscriptionCreate
    ) -> CompanySubscription:
        """Criar nova assinatura para empresa"""
        import structlog

        logger = structlog.get_logger()

        logger.info(
            "Iniciando criação de subscription",
            company_id=subscription_data.company_id,
            plan_id=subscription_data.plan_id,
        )

        # Verificar se já existe assinatura ativa
        existing = await self.repository.get_company_subscription(
            subscription_data.company_id
        )
        if existing:
            logger.warning(
                "Empresa já possui assinatura ativa",
                company_id=subscription_data.company_id,
                existing_subscription_id=existing.id,
            )
            raise ValueError("Empresa já possui assinatura ativa")

        # Buscar plano
        plan = await self.repository.get_subscription_plan_by_id(
            subscription_data.plan_id
        )
        if not plan or not plan.is_active:
            logger.error(
                "Plano não encontrado ou inativo", plan_id=subscription_data.plan_id
            )
            raise ValueError("Plano não encontrado ou inativo")

        # Criar assinatura
        subscription_dict = subscription_data.model_dump()
        logger.info("Dados do frontend", subscription_dict=subscription_dict)

        subscription_dict["status"] = "active"  # Garantir que status seja definido
        subscription_dict["created_at"] = datetime.now()

        logger.info("Dados para criação no banco", subscription_dict=subscription_dict)

        return await self.repository.create_company_subscription(subscription_dict)

    async def update_subscription_payment_method(
        self, company_id: int, payment_method: str, pagbank_data: Optional[dict] = None
    ) -> CompanySubscription:
        """Atualizar método de pagamento da assinatura"""
        subscription = await self.repository.get_company_subscription(company_id)
        if not subscription:
            raise ValueError("Assinatura não encontrada")

        update_data = {"payment_method": payment_method, "updated_at": datetime.now()}

        if pagbank_data and payment_method == "recurrent":
            update_data["pagbank_subscription_id"] = pagbank_data.get("subscription_id")

        return await self.repository.update_company_subscription(
            subscription.id, update_data
        )

    # ==========================================
    # INVOICE MANAGEMENT
    # ==========================================

    async def create_manual_invoice(
        self, invoice_request: CreateProTeamCareInvoiceRequest
    ) -> ProTeamCareInvoice:
        """Criar fatura manual para empresa"""
        # Buscar assinatura
        subscription = await self.repository.get_company_subscription(
            invoice_request.company_id
        )
        if not subscription:
            raise ValueError("Empresa não possui assinatura ativa")

        # Gerar número da fatura
        year = invoice_request.billing_period_start.year
        month = invoice_request.billing_period_start.month
        invoice_number = await self.repository.generate_invoice_number(
            invoice_request.company_id, year, month
        )

        # Criar fatura
        invoice_data = {
            "company_id": invoice_request.company_id,
            "subscription_id": subscription.id,
            "invoice_number": invoice_number,
            "amount": invoice_request.amount,
            "billing_period_start": invoice_request.billing_period_start,
            "billing_period_end": invoice_request.billing_period_end,
            "due_date": invoice_request.due_date,
            "status": "pending",
            "payment_method": "manual",
            "notes": invoice_request.notes,
            "created_at": datetime.now(),
        }

        return await self.repository.create_proteamcare_invoice(invoice_data)

    async def create_checkout_session(self, invoice_id: int) -> CheckoutSessionResponse:
        """Criar sessão de checkout PagBank para fatura"""
        import structlog

        logger = structlog.get_logger()

        logger.info("Iniciando criação de checkout session", invoice_id=invoice_id)

        # Buscar fatura
        invoice = await self.repository.get_proteamcare_invoice_by_id(invoice_id)
        if not invoice:
            logger.error("Fatura não encontrada", invoice_id=invoice_id)
            raise ValueError("Fatura não encontrada")

        logger.info(
            "Fatura encontrada",
            invoice_id=invoice_id,
            status=invoice.status,
            amount=invoice.amount,
            company_id=invoice.company_id,
        )

        if invoice.status != "pending":
            logger.error(
                "Fatura não está pendente",
                invoice_id=invoice_id,
                current_status=invoice.status,
            )
            raise ValueError("Fatura não está pendente")

        # Criar checkout no PagBank
        checkout_data = {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "contract_number": f"B2B-{invoice.company_id}",  # Identificador do contrato B2B
            "total_amount": float(invoice.amount),
            "customer_name": (
                invoice.company.people.name if invoice.company.people else "Empresa"
            ),
            "customer_email": "contato@proteamcare.com",  # Email padrão ou buscar do banco
            "customer_tax_id": (
                invoice.company.people.tax_id if invoice.company.people else None
            ),
            "customer_phone_area": "11",  # DDD padrão
            "customer_phone_number": "999999999",  # Telefone padrão
            "notification_urls": [
                "https://api.proteamcare.com/api/v1/b2b-billing/webhook/pagbank"
            ],
        }

        logger.info("Dados preparados para PagBank", checkout_data=checkout_data)

        try:
            checkout_response = await self.pagbank_service.create_checkout_session(
                checkout_data
            )
            logger.info(
                "Resposta do PagBank recebida",
                success=checkout_response.get("success", False),
                session_id=checkout_response.get("session_id"),
            )

            # Atualizar fatura com dados do checkout
            await self.repository.update_proteamcare_invoice(
                invoice_id,
                {
                    "pagbank_checkout_url": checkout_response["checkout_url"],
                    "pagbank_session_id": checkout_response["session_id"],
                    "updated_at": datetime.now(),
                },
            )

            return CheckoutSessionResponse(
                success=True,
                invoice_id=invoice_id,
                checkout_url=checkout_response["checkout_url"],
                session_id=checkout_response["session_id"],
                expires_at=checkout_response["expires_at"],
                qr_code=checkout_response.get("qr_code"),
                transaction_id=checkout_response.get("transaction_id"),
            )

        except Exception as e:
            logger.error(
                "Erro ao criar checkout session",
                invoice_id=invoice_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError(f"Erro ao criar checkout: {str(e)}")

    async def mark_invoice_as_paid(
        self,
        invoice_id: int,
        payment_method: str,
        payment_date: date,
        transaction_reference: Optional[str] = None,
    ) -> ProTeamCareInvoice:
        """Marcar fatura como paga"""
        update_data = {
            "status": "paid",
            "payment_method": payment_method,
            "paid_at": datetime.combine(payment_date, datetime.min.time()),
            "updated_at": datetime.now(),
        }

        if transaction_reference:
            update_data["pagbank_transaction_id"] = transaction_reference

        invoice = await self.repository.update_proteamcare_invoice(
            invoice_id, update_data
        )
        if not invoice:
            raise ValueError("Fatura não encontrada")

        return invoice

    # ==========================================
    # BULK OPERATIONS
    # ==========================================

    async def generate_monthly_invoices(
        self,
        target_month: int,
        target_year: int,
        company_ids: Optional[List[int]] = None,
    ) -> dict:
        """Gerar faturas mensais para todas as empresas ativas"""
        if company_ids:
            # Buscar assinaturas específicas
            subscriptions = []
            for company_id in company_ids:
                subscription = await self.repository.get_company_subscription(
                    company_id
                )
                if subscription:
                    subscriptions.append(subscription)
        else:
            # Buscar todas as assinaturas ativas
            subscriptions = await self.repository.get_all_active_subscriptions()

        total_companies = len(subscriptions)
        invoices_created = 0
        invoices_failed = 0
        total_amount = Decimal("0.00")
        errors = []

        # Calcular período de faturamento
        billing_period_start = date(target_year, target_month, 1)
        if target_month == 12:
            billing_period_end = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            billing_period_end = date(target_year, target_month + 1, 1) - timedelta(
                days=1
            )

        for subscription in subscriptions:
            try:
                # Calcular data de vencimento baseada no billing_day
                if subscription.billing_day <= billing_period_end.day:
                    due_date = date(target_year, target_month, subscription.billing_day)
                else:
                    # Se o dia não existe no mês, usar último dia do mês
                    due_date = billing_period_end

                # Verificar se já existe fatura para este período
                existing_invoices = await self.repository.get_company_invoices(
                    subscription.company_id, status=None, limit=5
                )

                invoice_exists = any(
                    inv.billing_period_start.month == target_month
                    and inv.billing_period_start.year == target_year
                    for inv in existing_invoices
                )

                if invoice_exists:
                    errors.append(
                        f"Fatura já existe para empresa ID {subscription.company_id}"
                    )
                    invoices_failed += 1
                    continue

                # Gerar número da fatura
                invoice_number = await self.repository.generate_invoice_number(
                    subscription.company_id, target_year, target_month
                )

                # Criar fatura
                invoice_data = {
                    "company_id": subscription.company_id,
                    "subscription_id": subscription.id,
                    "invoice_number": invoice_number,
                    "amount": subscription.plan.monthly_price,
                    "billing_period_start": billing_period_start,
                    "billing_period_end": billing_period_end,
                    "due_date": due_date,
                    "status": "pending",
                    "payment_method": subscription.payment_method,
                    "created_at": datetime.now(),
                }

                await self.repository.create_proteamcare_invoice(invoice_data)
                invoices_created += 1
                total_amount += subscription.plan.monthly_price

            except Exception as e:
                errors.append(f"Erro na empresa ID {subscription.company_id}: {str(e)}")
                invoices_failed += 1

        return {
            "success": invoices_failed == 0,
            "total_companies": total_companies,
            "invoices_created": invoices_created,
            "invoices_failed": invoices_failed,
            "total_amount": total_amount,
            "errors": errors,
        }

    # ==========================================
    # DASHBOARD DATA
    # ==========================================

    async def get_dashboard_data(self) -> dict:
        """Buscar dados do dashboard B2B"""
        # Métricas principais
        metrics = await self.repository.get_billing_metrics()

        # Status das empresas
        companies_status = await self.repository.get_companies_billing_status()

        # Faturas recentes
        recent_payments = await self.repository.get_invoices_by_status("paid", limit=10)

        # Distribuição por planos
        plan_distribution = await self.repository.get_plan_distribution()

        return {
            "metrics": metrics,
            "companies_status": companies_status,
            "recent_payments": recent_payments,
            "plan_distribution": plan_distribution,
        }

    async def get_overdue_invoices(self) -> List[ProTeamCareInvoice]:
        """Buscar faturas vencidas"""
        return await self.repository.get_overdue_invoices()

    # ==========================================
    # WEBHOOK PROCESSING
    # ==========================================

    async def process_pagbank_webhook(self, webhook_data: dict) -> bool:
        """Processar webhook do PagBank para faturas B2B"""
        try:
            # Extrair dados do webhook
            event_type = webhook_data.get("event_type")
            transaction_data = webhook_data.get("data", {})
            session_id = transaction_data.get("session_id")

            if not session_id:
                return False

            # Buscar fatura pelo session_id
            # Implementar busca por session_id
            # Por simplicidade, vou assumir que temos o invoice_id no webhook
            invoice_id = transaction_data.get(
                "reference_id"
            )  # Assumindo que enviamos o invoice_id como reference

            if not invoice_id:
                return False

            invoice = await self.repository.get_proteamcare_invoice_by_id(
                int(invoice_id)
            )
            if not invoice:
                return False

            # Processar diferentes tipos de eventos
            if event_type == "payment.approved":
                await self.repository.update_proteamcare_invoice(
                    invoice.id,
                    {
                        "status": "paid",
                        "paid_at": datetime.now(),
                        "pagbank_transaction_id": transaction_data.get(
                            "transaction_id"
                        ),
                        "updated_at": datetime.now(),
                    },
                )

            elif event_type == "payment.declined":
                await self.repository.update_proteamcare_invoice(
                    invoice.id,
                    {
                        "status": "pending",  # Manter como pendente para nova tentativa
                        "notes": f"Pagamento recusado: {transaction_data.get('decline_reason', 'Motivo não informado')}",
                        "updated_at": datetime.now(),
                    },
                )

            return True

        except Exception as e:
            print(f"Erro processando webhook PagBank B2B: {str(e)}")
            return False
