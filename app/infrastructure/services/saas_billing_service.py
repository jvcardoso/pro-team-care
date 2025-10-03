from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.infrastructure.repositories.saas_billing_repository import SaasBillingRepository
from app.infrastructure.services.pagbank_service import PagBankService
from app.infrastructure.orm.models import (
    CompanySubscription,
    ProTeamCareInvoice,
    SubscriptionPlan,
    Company,
    Establishments,
)

logger = structlog.get_logger()


class SaasBillingService:
    """Service for SaaS billing (Company Subscriptions)"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.saas_billing_repository = SaasBillingRepository(db)
        self.pagbank_service = PagBankService()

    # ==========================================
    # AUTOMATIC BILLING METHODS
    # ==========================================

    async def run_automatic_saas_billing(
        self,
        billing_date: Optional[date] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Run automatic SaaS billing process for all due subscriptions"""
        try:
            if billing_date is None:
                billing_date = date.today()

            logger.info(
                "Starting automatic SaaS billing process",
                billing_date=billing_date,
                force_regenerate=force_regenerate
            )

            # Get all subscriptions that are due for billing
            due_subscriptions = await self._get_due_saas_subscriptions(billing_date)

            generated_invoices = []
            errors = []
            successful = 0

            for subscription in due_subscriptions:
                try:
                    invoice = await self._generate_saas_invoice_for_subscription(
                        subscription, billing_date, force_regenerate
                    )
                    if invoice:
                        generated_invoices.append(invoice.id)
                        successful += 1
                        logger.info(
                            "SaaS invoice generated successfully",
                            subscription_id=subscription.id,
                            company_id=subscription.company_id,
                            invoice_id=invoice.id
                        )
                except Exception as e:
                    error_msg = f"Error generating SaaS invoice for subscription {subscription.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(
                        "SaaS invoice generation failed",
                        error=error_msg,
                        subscription_id=subscription.id
                    )

            # Update overdue invoices status
            await self._update_overdue_saas_invoices()

            result = {
                "total_subscriptions_processed": len(due_subscriptions),
                "successful_invoices": successful,
                "failed_invoices": len(errors),
                "generated_invoice_ids": generated_invoices,
                "errors": errors,
                "billing_date": billing_date.isoformat(),
            }

            logger.info("Automatic SaaS billing process completed", result=result)
            return result

        except Exception as e:
            logger.error("Automatic SaaS billing process failed", error=str(e))
            raise

    async def _get_due_saas_subscriptions(self, billing_date: date) -> List[CompanySubscription]:
        """Get all subscriptions that are due for billing"""
        try:
            current_day = billing_date.day

            # Get subscriptions where billing_day matches current day or has passed
            query = (
                select(CompanySubscription)
                .where(
                    and_(
                        CompanySubscription.status == "active",
                        CompanySubscription.billing_day <= current_day
                    )
                )
            )

            result = await self.db.execute(query)
            subscriptions = result.scalars().all()

            # Filter subscriptions that don't have an invoice for current period
            due_subscriptions = []
            for subscription in subscriptions:
                # Check if invoice already exists for current month
                period_start = billing_date.replace(day=1)
                next_month = (period_start.replace(month=period_start.month + 1)
                             if period_start.month < 12
                             else period_start.replace(year=period_start.year + 1, month=1))
                period_end = next_month - timedelta(days=1)

                existing_invoice_query = (
                    select(ProTeamCareInvoice)
                    .where(
                        and_(
                            ProTeamCareInvoice.subscription_id == subscription.id,
                            ProTeamCareInvoice.billing_period_start >= period_start,
                            ProTeamCareInvoice.billing_period_end <= period_end
                        )
                    )
                )
                existing_result = await self.db.execute(existing_invoice_query)
                existing_invoice = existing_result.scalar_one_or_none()

                if not existing_invoice:
                    due_subscriptions.append(subscription)

            logger.info(
                "Found due SaaS subscriptions",
                total_active=len(subscriptions),
                due_count=len(due_subscriptions)
            )

            return due_subscriptions

        except Exception as e:
            logger.error("Error getting due SaaS subscriptions", error=str(e))
            raise

    async def _generate_saas_invoice_for_subscription(
        self,
        subscription: CompanySubscription,
        billing_date: date,
        force_regenerate: bool = False
    ) -> Optional[ProTeamCareInvoice]:
        """Generate SaaS invoice for a subscription"""
        try:
            # Calculate billing period (monthly)
            period_start = billing_date.replace(day=1)
            next_month = (period_start.replace(month=period_start.month + 1)
                         if period_start.month < 12
                         else period_start.replace(year=period_start.year + 1, month=1))
            period_end = next_month - timedelta(days=1)

            # Check for existing invoice unless force regenerate
            if not force_regenerate:
                existing_invoice_query = (
                    select(ProTeamCareInvoice)
                    .where(
                        and_(
                            ProTeamCareInvoice.subscription_id == subscription.id,
                            ProTeamCareInvoice.billing_period_start >= period_start,
                            ProTeamCareInvoice.billing_period_end <= period_end
                        )
                    )
                )
                existing_result = await self.db.execute(existing_invoice_query)
                existing_invoice = existing_result.scalar_one_or_none()

                if existing_invoice:
                    logger.info(
                        "Invoice already exists for subscription",
                        subscription_id=subscription.id,
                        invoice_id=existing_invoice.id
                    )
                    return None

            # Calculate amount based on establishments
            amount = await self.saas_billing_repository.calculate_subscription_amount(subscription.id)

            # Calculate due date (30 days from billing date)
            due_date = billing_date + timedelta(days=30)

            # Create invoice
            invoice_data = {
                "company_id": subscription.company_id,
                "subscription_id": subscription.id,
                "amount": amount,
                "billing_period_start": period_start,
                "billing_period_end": period_end,
                "due_date": due_date,
                "status": "pending",
                "payment_method": subscription.payment_method,
            }

            # If recurrent payment, try to charge immediately
            if subscription.payment_method == "recurrent" and subscription.pagbank_subscription_id:
                try:
                    payment_result = await self.pagbank_service.charge_subscription(
                        subscription.pagbank_subscription_id,
                        amount,
                        f"Pro Team Care - {period_start.strftime('%m/%Y')}"
                    )

                    if payment_result.get("success"):
                        invoice_data["status"] = "paid"
                        invoice_data["paid_at"] = datetime.utcnow()
                        invoice_data["pagbank_transaction_id"] = payment_result.get("transaction_id")
                    else:
                        invoice_data["status"] = "pending"
                        logger.warning(
                            "Recurrent payment failed, creating manual invoice",
                            subscription_id=subscription.id,
                            error=payment_result.get("error")
                        )
                except Exception as e:
                    logger.error(
                        "Error processing recurrent payment",
                        error=str(e),
                        subscription_id=subscription.id
                    )
                    invoice_data["status"] = "pending"

            invoice = await self.saas_billing_repository.create_saas_invoice(invoice_data)

            logger.info(
                "SaaS invoice generated successfully",
                subscription_id=subscription.id,
                invoice_id=invoice.id,
                amount=amount,
                period_start=period_start,
                period_end=period_end
            )

            return invoice

        except Exception as e:
            logger.error(
                "Error generating SaaS invoice for subscription",
                error=str(e),
                subscription_id=subscription.id
            )
            raise

    async def _update_overdue_saas_invoices(self) -> None:
        """Update status of overdue SaaS invoices"""
        try:
            today = date.today()

            # Update pending/sent invoices that are past due date to 'overdue'
            overdue_invoices = await self.saas_billing_repository.list_saas_invoices(
                status=None,  # Don't filter by status in the query
                overdue_only=True,  # This will filter for overdue
                size=1000  # Process up to 1000 at once
            )

            updated_count = 0
            for invoice in overdue_invoices["invoices"]:
                if invoice.status in ["pending", "sent"] and invoice.due_date < today:
                    await self.saas_billing_repository.update_saas_invoice_status(
                        invoice.id,
                        "overdue"
                    )
                    updated_count += 1

            if updated_count > 0:
                logger.info("Updated overdue SaaS invoices", count=updated_count)

        except Exception as e:
            logger.error("Error updating overdue SaaS invoices", error=str(e))

    # ==========================================
    # SUBSCRIPTION MANAGEMENT
    # ==========================================

    async def create_subscription(
        self,
        company_id: int,
        plan_id: int,
        billing_day: int = 1,
        payment_method: str = "manual",
        auto_renew: bool = True,
        send_activation_email: bool = True,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> CompanySubscription:
        """Create a new company subscription and optionally send activation email"""
        try:
            # Check if company already has an active subscription
            existing_subscription = await self.saas_billing_repository.get_subscription_by_company(company_id)
            if existing_subscription:
                raise ValueError(f"Company {company_id} already has an active subscription")

            subscription_data = {
                "company_id": company_id,
                "plan_id": plan_id,
                "status": "active",
                "start_date": date.today(),
                "billing_day": billing_day,
                "payment_method": payment_method,
                "auto_renew": auto_renew,
            }

            subscription = await self.saas_billing_repository.create_subscription(subscription_data)

            logger.info(
                "Subscription created successfully",
                subscription_id=subscription.id,
                company_id=company_id,
                plan_id=plan_id
            )

            # 🔥 NOVO: Enviar email de ativação automaticamente
            if send_activation_email:
                try:
                    await self._send_activation_email_after_subscription(
                        company_id=company_id,
                        subscription=subscription,
                        recipient_email=recipient_email,
                        recipient_name=recipient_name
                    )
                except Exception as email_error:
                    # Log erro mas não falha a criação da assinatura
                    logger.warning(
                        "Failed to send activation email but subscription was created",
                        error=str(email_error),
                        subscription_id=subscription.id,
                        company_id=company_id
                    )

            return subscription

        except Exception as e:
            logger.error("Error creating subscription", error=str(e))
            raise

    async def setup_recurrent_billing(
        self,
        subscription_id: int,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Setup recurrent billing for a subscription"""
        try:
            subscription = await self.saas_billing_repository.get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            # Create PagBank customer and subscription
            pagbank_result = await self.pagbank_service.create_subscription(
                customer_data=customer_data,
                plan_data={
                    "name": f"Pro Team Care - {subscription.plan.name}",
                    "amount": await self.saas_billing_repository.calculate_subscription_amount(subscription_id),
                    "interval": "MONTH",
                    "billing_day": subscription.billing_day,
                }
            )

            if not pagbank_result.get("success"):
                raise Exception(f"Failed to create PagBank subscription: {pagbank_result.get('error')}")

            # Update subscription with PagBank data
            await self.saas_billing_repository.update_subscription_payment_method(
                subscription_id,
                "recurrent",
                pagbank_result.get("subscription_id")
            )

            result = {
                "success": True,
                "subscription_id": subscription_id,
                "pagbank_subscription_id": pagbank_result.get("subscription_id"),
                "pagbank_customer_id": pagbank_result.get("customer_id"),
            }

            logger.info(
                "Recurrent billing setup successfully",
                subscription_id=subscription_id,
                pagbank_subscription_id=result["pagbank_subscription_id"]
            )

            return result

        except Exception as e:
            logger.error("Error setting up recurrent billing", error=str(e), subscription_id=subscription_id)
            raise

    async def cancel_subscription(
        self,
        subscription_id: int,
        cancel_pagbank: bool = True
    ) -> CompanySubscription:
        """Cancel a subscription"""
        try:
            subscription = await self.saas_billing_repository.get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            # Cancel PagBank subscription if exists
            if cancel_pagbank and subscription.pagbank_subscription_id:
                try:
                    await self.pagbank_service.cancel_subscription(subscription.pagbank_subscription_id)
                except Exception as e:
                    logger.warning(
                        "Failed to cancel PagBank subscription",
                        error=str(e),
                        pagbank_subscription_id=subscription.pagbank_subscription_id
                    )

            # Update subscription status
            updated_subscription = await self.saas_billing_repository.update_subscription(
                subscription_id,
                {
                    "status": "cancelled",
                    "end_date": date.today(),
                }
            )

            logger.info(
                "Subscription cancelled successfully",
                subscription_id=subscription_id,
                company_id=subscription.company_id
            )

            return updated_subscription

        except Exception as e:
            logger.error("Error cancelling subscription", error=str(e), subscription_id=subscription_id)
            raise

    # ==========================================
    # INVOICE PROCESSING
    # ==========================================

    async def process_manual_payment(
        self,
        invoice_id: int,
        payment_method: str,
        payment_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ProTeamCareInvoice:
        """Process manual payment for an invoice"""
        try:
            invoice = await self.saas_billing_repository.get_saas_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            if invoice.status == "paid":
                raise ValueError(f"Invoice {invoice_id} is already paid")

            # Update invoice status
            updated_invoice = await self.saas_billing_repository.update_saas_invoice_status(
                invoice_id,
                "paid",
                paid_at=datetime.utcnow(),
                payment_method=payment_method,
                notes=notes
            )

            logger.info(
                "Manual payment processed successfully",
                invoice_id=invoice_id,
                payment_method=payment_method
            )

            return updated_invoice

        except Exception as e:
            logger.error("Error processing manual payment", error=str(e), invoice_id=invoice_id)
            raise

    async def generate_payment_link(self, invoice_id: int) -> Dict[str, Any]:
        """Generate payment link for an invoice"""
        try:
            invoice = await self.saas_billing_repository.get_saas_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            if invoice.status == "paid":
                raise ValueError(f"Invoice {invoice_id} is already paid")

            # Create PagBank checkout session
            checkout_data = {
                "amount": invoice.amount,
                "description": f"Pro Team Care - Fatura {invoice.invoice_number}",
                "reference_id": f"saas_invoice_{invoice.id}",
                "customer": {
                    "name": invoice.company.name,
                    "email": invoice.company.email or "contato@proteamcare.com",
                    "document": invoice.company.tax_id,
                },
                "notification_urls": [
                    f"{os.getenv('BASE_URL', 'https://api.proteamcare.com')}/api/v1/webhooks/pagbank"
                ]
            }

            pagbank_result = await self.pagbank_service.create_checkout_session(checkout_data)

            if not pagbank_result.get("success"):
                raise Exception(f"Failed to create payment link: {pagbank_result.get('error')}")

            # Update invoice with PagBank data
            await self.saas_billing_repository.update_saas_invoice(
                invoice_id,
                {
                    "pagbank_checkout_url": pagbank_result.get("checkout_url"),
                    "pagbank_session_id": pagbank_result.get("session_id"),
                    "status": "sent" if invoice.status == "pending" else invoice.status,
                }
            )

            result = {
                "success": True,
                "invoice_id": invoice_id,
                "checkout_url": pagbank_result.get("checkout_url"),
                "session_id": pagbank_result.get("session_id"),
            }

            logger.info(
                "Payment link generated successfully",
                invoice_id=invoice_id,
                checkout_url=result["checkout_url"]
            )

            return result

        except Exception as e:
            logger.error("Error generating payment link", error=str(e), invoice_id=invoice_id)
            raise

    # ==========================================
    # WEBHOOK PROCESSING
    # ==========================================

    async def process_pagbank_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PagBank webhook for SaaS payments"""
        try:
            event_type = webhook_data.get("event_type")
            charge_data = webhook_data.get("charges", [{}])[0]
            reference_id = charge_data.get("reference_id", "")

            logger.info(
                "Processing PagBank webhook for SaaS",
                event_type=event_type,
                reference_id=reference_id
            )

            # Only process SaaS invoice webhooks
            if not reference_id.startswith("saas_invoice_"):
                return {"success": False, "error": "Not a SaaS invoice webhook"}

            invoice_id = int(reference_id.replace("saas_invoice_", ""))
            invoice = await self.saas_billing_repository.get_saas_invoice_by_id(invoice_id)

            if not invoice:
                return {"success": False, "error": f"Invoice {invoice_id} not found"}

            # Process based on event type
            if event_type == "CHARGE.PAID":
                # Payment successful
                await self.saas_billing_repository.update_saas_invoice_status(
                    invoice_id,
                    "paid",
                    paid_at=datetime.utcnow(),
                    payment_method="pagbank",
                    pagbank_transaction_id=charge_data.get("id"),
                    notes=f"Paid via PagBank webhook - Charge ID: {charge_data.get('id')}"
                )

                logger.info(
                    "SaaS invoice marked as paid via webhook",
                    invoice_id=invoice_id,
                    charge_id=charge_data.get("id")
                )

            elif event_type in ["CHARGE.DECLINED", "CHARGE.CANCELED"]:
                # Payment failed
                await self.saas_billing_repository.update_saas_invoice_status(
                    invoice_id,
                    "pending",
                    notes=f"Payment {event_type.lower()} - Charge ID: {charge_data.get('id')}"
                )

                logger.info(
                    "SaaS invoice payment failed via webhook",
                    invoice_id=invoice_id,
                    event_type=event_type,
                    charge_id=charge_data.get("id")
                )

            return {"success": True, "invoice_id": invoice_id}

        except Exception as e:
            logger.error("Error processing PagBank webhook for SaaS", error=str(e))
            return {"success": False, "error": str(e)}

    # ==========================================
    # ANALYTICS AND REPORTING
    # ==========================================

    async def get_saas_dashboard_metrics(self) -> Dict[str, Any]:
        """Get SaaS billing dashboard metrics"""
        try:
            metrics = await self.saas_billing_repository.get_saas_billing_dashboard_metrics()

            # Calculate additional metrics
            current_month_start = date.today().replace(day=1)

            # MRR (Monthly Recurring Revenue) - based on active subscriptions
            active_subscriptions = await self.saas_billing_repository.list_subscriptions(
                status="active",
                size=1000
            )

            total_mrr = Decimal("0")
            for subscription in active_subscriptions["subscriptions"]:
                subscription_amount = await self.saas_billing_repository.calculate_subscription_amount(
                    subscription.id
                )
                total_mrr += subscription_amount

            metrics["monthly_recurring_revenue"] = total_mrr
            metrics["average_revenue_per_user"] = (
                total_mrr / metrics["total_active_subscriptions"]
                if metrics["total_active_subscriptions"] > 0
                else Decimal("0")
            ).quantize(Decimal("0.01"))

            logger.info("SaaS dashboard metrics calculated", metrics=metrics)
            return metrics

        except Exception as e:
            logger.error("Error getting SaaS dashboard metrics", error=str(e))
            raise

    async def get_monthly_revenue_report(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly revenue report for SaaS"""
        try:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            # Get invoices for the period
            invoices_data = await self.saas_billing_repository.list_saas_invoices(
                start_date=start_date,
                end_date=end_date,
                size=1000
            )

            total_billed = Decimal("0")
            total_paid = Decimal("0")
            total_pending = Decimal("0")
            total_overdue = Decimal("0")

            for invoice in invoices_data["invoices"]:
                total_billed += invoice.amount

                if invoice.status == "paid":
                    total_paid += invoice.amount
                elif invoice.status in ["pending", "sent"]:
                    if invoice.due_date < date.today():
                        total_overdue += invoice.amount
                    else:
                        total_pending += invoice.amount

            report = {
                "period": f"{year}-{month:02d}",
                "total_billed": total_billed,
                "total_paid": total_paid,
                "total_pending": total_pending,
                "total_overdue": total_overdue,
                "collection_rate": (
                    (total_paid / total_billed * 100)
                    if total_billed > 0
                    else Decimal("0")
                ).quantize(Decimal("0.01")),
                "invoices_count": len(invoices_data["invoices"]),
            }

            logger.info("Monthly revenue report generated", report=report)
            return report

        except Exception as e:
            logger.error("Error generating monthly revenue report", error=str(e))
            raise

    # ==========================================
    # ACTIVATION EMAIL (NEW FLOW)
    # ==========================================

    async def _send_activation_email_after_subscription(
        self,
        company_id: int,
        subscription: CompanySubscription,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ):
        """
        Envia email de ativação automaticamente após criar assinatura

        Fluxo:
        1. Se recipient_email fornecido → usa ele
        2. Se não → busca emails cadastrados na empresa
        3. Chama use case de ativação para enviar email
        """
        from app.application.use_cases.company_activation_use_case import CompanyActivationUseCase
        from sqlalchemy import select
        from app.infrastructure.orm.models import Email, People

        try:
            # 1. Determinar email e nome do destinatário
            email_to_use = recipient_email
            name_to_use = recipient_name

            # Se não forneceu email, busca emails cadastrados
            if not email_to_use:
                # Buscar company com person
                company_query = select(Company).where(Company.id == company_id)
                company_result = await self.db.execute(company_query)
                company = company_result.scalar_one_or_none()

                if company and company.person_id:
                    # Buscar emails da pessoa/empresa
                    email_query = (
                        select(Email)
                        .where(Email.emailable_id == company.person_id)
                        .where(Email.emailable_type == 'person')
                        .where(Email.is_active == True)
                        .order_by(Email.is_principal.desc())  # Principal primeiro
                    )
                    email_result = await self.db.execute(email_query)
                    first_email = email_result.scalar_one_or_none()

                    if first_email:
                        email_to_use = first_email.email_address

                        # Buscar nome da empresa
                        person_query = select(People).where(People.id == company.person_id)
                        person_result = await self.db.execute(person_query)
                        person = person_result.scalar_one_or_none()

                        if person and not name_to_use:
                            name_to_use = person.name or "Responsável"

            # 2. Validar se tem email
            if not email_to_use:
                logger.warning(
                    "Cannot send activation email: no email provided or found",
                    company_id=company_id,
                    subscription_id=subscription.id
                )
                return

            # 3. Usar nome padrão se não fornecido
            if not name_to_use:
                name_to_use = "Responsável"

            # 4. Chamar use case de ativação
            activation_use_case = CompanyActivationUseCase(self.db)
            result = await activation_use_case.send_contract_email(
                company_id=company_id,
                recipient_email=email_to_use,
                recipient_name=name_to_use
            )

            logger.info(
                "Activation email sent successfully after subscription creation",
                company_id=company_id,
                subscription_id=subscription.id,
                recipient_email=email_to_use,
                success=result.get("success", False)
            )

        except Exception as e:
            logger.error(
                "Failed to send activation email",
                error=str(e),
                company_id=company_id,
                subscription_id=subscription.id
            )
            # Não propaga o erro - apenas loga
            raise