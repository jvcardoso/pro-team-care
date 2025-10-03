from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import Integer, and_, func, or_, select, text, update, desc
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.orm.models import (
    Company,
    CompanySubscription,
    SubscriptionPlan,
    ProTeamCareInvoice,
    Establishments,
    PagBankTransaction,
)
from app.infrastructure.services.tenant_context_service import get_tenant_context

logger = structlog.get_logger()


class SaasBillingRepository:
    """Repository for SaaS billing (Company Subscriptions)"""

    def __init__(self, db):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, "replace"):
            return dt.replace(tzinfo=None)
        return dt

    # ==========================================
    # SUBSCRIPTION METHODS
    # ==========================================

    async def create_subscription(self, subscription_data: Dict[str, Any]) -> CompanySubscription:
        """Create a new company subscription"""
        try:
            subscription = CompanySubscription(
                company_id=subscription_data["company_id"],
                plan_id=subscription_data["plan_id"],
                status=subscription_data.get("status", "active"),
                start_date=subscription_data["start_date"],
                end_date=subscription_data.get("end_date"),
                billing_day=subscription_data.get("billing_day", 1),
                payment_method=subscription_data.get("payment_method", "manual"),
                pagbank_subscription_id=subscription_data.get("pagbank_subscription_id"),
                auto_renew=subscription_data.get("auto_renew", True),
            )

            self.db.add(subscription)
            await self.db.flush()
            await self.db.refresh(subscription)

            logger.info(
                "Company subscription created successfully",
                subscription_id=subscription.id,
                company_id=subscription.company_id,
            )

            return subscription

        except Exception as e:
            logger.error("Error creating subscription", error=str(e), subscription_data=subscription_data)
            raise

    async def get_subscription_by_id(self, subscription_id: int) -> Optional[CompanySubscription]:
        """Get subscription by ID"""
        try:
            query = (
                select(CompanySubscription)
                .options(
                    joinedload(CompanySubscription.company),
                    joinedload(CompanySubscription.plan)
                )
                .where(CompanySubscription.id == subscription_id)
            )

            result = await self.db.execute(query)
            subscription = result.unique().scalar_one_or_none()

            if subscription:
                logger.info("Subscription retrieved successfully", subscription_id=subscription_id)
            else:
                logger.warning("Subscription not found", subscription_id=subscription_id)

            return subscription

        except Exception as e:
            logger.error("Error retrieving subscription", error=str(e), subscription_id=subscription_id)
            raise

    async def get_subscription_by_company(self, company_id: int) -> Optional[CompanySubscription]:
        """Get active subscription by company ID"""
        try:
            query = (
                select(CompanySubscription)
                .options(
                    joinedload(CompanySubscription.company),
                    joinedload(CompanySubscription.plan)
                )
                .where(
                    and_(
                        CompanySubscription.company_id == company_id,
                        CompanySubscription.status == "active"
                    )
                )
            )

            result = await self.db.execute(query)
            subscription = result.unique().scalar_one_or_none()

            return subscription

        except Exception as e:
            logger.error("Error retrieving subscription by company", error=str(e), company_id=company_id)
            raise

    async def list_subscriptions(
        self,
        company_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        status: Optional[str] = None,
        payment_method: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List subscriptions with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(CompanySubscription).options(
                joinedload(CompanySubscription.company),
                joinedload(CompanySubscription.plan)
            )

            # Apply filters
            filters = []
            if company_id:
                filters.append(CompanySubscription.company_id == company_id)
            if plan_id:
                filters.append(CompanySubscription.plan_id == plan_id)
            if status:
                filters.append(CompanySubscription.status == status)
            if payment_method:
                filters.append(CompanySubscription.payment_method == payment_method)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(CompanySubscription.id))
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(desc(CompanySubscription.created_at)).offset(offset).limit(size)
            result = await self.db.execute(query)
            subscriptions = result.unique().scalars().all()

            logger.info(
                "Subscriptions listed successfully",
                total=total,
                page=page,
                size=size,
            )

            return {
                "subscriptions": subscriptions,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing subscriptions", error=str(e))
            raise

    async def update_subscription(self, subscription_id: int, update_data: Dict[str, Any]) -> Optional[CompanySubscription]:
        """Update subscription"""
        try:
            update_data_with_timestamp = update_data.copy()
            update_data_with_timestamp["updated_at"] = datetime.utcnow()

            stmt = (
                update(CompanySubscription)
                .where(CompanySubscription.id == subscription_id)
                .values(**update_data_with_timestamp)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated subscription
            subscription = await self.get_subscription_by_id(subscription_id)

            logger.info("Subscription updated successfully", subscription_id=subscription_id)
            return subscription

        except Exception as e:
            logger.error("Error updating subscription", error=str(e), subscription_id=subscription_id)
            raise

    # ==========================================
    # INVOICE METHODS
    # ==========================================

    async def _generate_saas_invoice_number(self, company_id: int) -> str:
        """Generate unique invoice number for SaaS billing"""
        try:
            now = datetime.now()
            year_month = now.strftime("%Y%m")

            # Find highest sequential number for this company and month
            query = select(func.count(ProTeamCareInvoice.id)).where(
                and_(
                    ProTeamCareInvoice.company_id == company_id,
                    func.extract('year', ProTeamCareInvoice.created_at) == now.year,
                    func.extract('month', ProTeamCareInvoice.created_at) == now.month
                )
            )
            result = await self.db.execute(query)
            count = result.scalar() or 0

            sequential = count + 1
            invoice_number = f"SAAS-{year_month}-{company_id:06d}-{sequential:03d}"

            logger.info(
                "Generated SaaS invoice number",
                company_id=company_id,
                invoice_number=invoice_number,
                sequential=sequential,
            )

            return invoice_number

        except Exception as e:
            logger.error("Error generating SaaS invoice number", error=str(e), company_id=company_id)
            raise

    async def create_saas_invoice(self, invoice_data: Dict[str, Any]) -> ProTeamCareInvoice:
        """Create a new SaaS invoice"""
        try:
            # Generate invoice number if not provided
            invoice_number = invoice_data.get("invoice_number")
            if not invoice_number:
                invoice_number = await self._generate_saas_invoice_number(invoice_data["company_id"])

            invoice = ProTeamCareInvoice(
                company_id=invoice_data["company_id"],
                subscription_id=invoice_data["subscription_id"],
                invoice_number=invoice_number,
                amount=invoice_data["amount"],
                billing_period_start=invoice_data["billing_period_start"],
                billing_period_end=invoice_data["billing_period_end"],
                due_date=invoice_data["due_date"],
                status=invoice_data.get("status", "pending"),
                payment_method=invoice_data.get("payment_method", "manual"),
                pagbank_checkout_url=invoice_data.get("pagbank_checkout_url"),
                pagbank_session_id=invoice_data.get("pagbank_session_id"),
                pagbank_transaction_id=invoice_data.get("pagbank_transaction_id"),
                notes=invoice_data.get("notes"),
            )

            self.db.add(invoice)
            await self.db.flush()
            await self.db.refresh(invoice)

            logger.info(
                "SaaS invoice created successfully",
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                company_id=invoice.company_id,
                subscription_id=invoice.subscription_id,
            )

            return invoice

        except Exception as e:
            logger.error("Error creating SaaS invoice", error=str(e), invoice_data=invoice_data)
            raise

    async def get_saas_invoice_by_id(self, invoice_id: int) -> Optional[ProTeamCareInvoice]:
        """Get SaaS invoice by ID with related data"""
        try:
            query = (
                select(ProTeamCareInvoice)
                .options(
                    joinedload(ProTeamCareInvoice.company),
                    joinedload(ProTeamCareInvoice.subscription).joinedload(CompanySubscription.plan),
                )
                .where(ProTeamCareInvoice.id == invoice_id)
            )

            result = await self.db.execute(query)
            invoice = result.unique().scalar_one_or_none()

            if invoice:
                logger.info("SaaS invoice retrieved successfully", invoice_id=invoice_id)
            else:
                logger.warning("SaaS invoice not found", invoice_id=invoice_id)

            return invoice

        except Exception as e:
            logger.error("Error retrieving SaaS invoice", error=str(e), invoice_id=invoice_id)
            raise

    async def list_saas_invoices(
        self,
        company_id: Optional[int] = None,
        subscription_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        overdue_only: Optional[bool] = False,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List SaaS invoices with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(ProTeamCareInvoice).options(
                joinedload(ProTeamCareInvoice.company),
                joinedload(ProTeamCareInvoice.subscription).joinedload(CompanySubscription.plan)
            )

            # Apply filters
            filters = []
            if company_id:
                filters.append(ProTeamCareInvoice.company_id == company_id)
            if subscription_id:
                filters.append(ProTeamCareInvoice.subscription_id == subscription_id)
            if status:
                filters.append(ProTeamCareInvoice.status == status)
            if start_date:
                filters.append(ProTeamCareInvoice.billing_period_start >= start_date)
            if end_date:
                filters.append(ProTeamCareInvoice.billing_period_end <= end_date)
            if overdue_only:
                filters.append(
                    and_(
                        ProTeamCareInvoice.due_date < date.today(),
                        ProTeamCareInvoice.status.in_(["pending", "sent"])
                    )
                )

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(ProTeamCareInvoice.id))
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(desc(ProTeamCareInvoice.created_at)).offset(offset).limit(size)
            result = await self.db.execute(query)
            invoices = result.unique().scalars().all()

            logger.info(
                "SaaS invoices listed successfully",
                total=total,
                page=page,
                size=size,
            )

            return {
                "invoices": invoices,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing SaaS invoices", error=str(e))
            raise

    async def update_saas_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> Optional[ProTeamCareInvoice]:
        """Update SaaS invoice"""
        try:
            update_data_with_timestamp = update_data.copy()
            update_data_with_timestamp["updated_at"] = datetime.utcnow()

            stmt = (
                update(ProTeamCareInvoice)
                .where(ProTeamCareInvoice.id == invoice_id)
                .values(**update_data_with_timestamp)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated invoice
            invoice = await self.get_saas_invoice_by_id(invoice_id)

            logger.info("SaaS invoice updated successfully", invoice_id=invoice_id)
            return invoice

        except Exception as e:
            logger.error("Error updating SaaS invoice", error=str(e), invoice_id=invoice_id)
            raise

    async def update_saas_invoice_status(self, invoice_id: int, status: str, **kwargs) -> Optional[ProTeamCareInvoice]:
        """Update SaaS invoice status with optional payment details"""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            # Add payment-related fields if provided
            if "paid_at" in kwargs:
                update_data["paid_at"] = kwargs["paid_at"]
            if "payment_method" in kwargs:
                update_data["payment_method"] = kwargs["payment_method"]
            if "pagbank_transaction_id" in kwargs:
                update_data["pagbank_transaction_id"] = kwargs["pagbank_transaction_id"]
            if "notes" in kwargs:
                update_data["notes"] = kwargs["notes"]

            stmt = (
                update(ProTeamCareInvoice)
                .where(ProTeamCareInvoice.id == invoice_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated invoice
            invoice = await self.get_saas_invoice_by_id(invoice_id)

            logger.info("SaaS invoice status updated successfully", invoice_id=invoice_id, status=status)
            return invoice

        except Exception as e:
            logger.error("Error updating SaaS invoice status", error=str(e), invoice_id=invoice_id)
            raise

    # ==========================================
    # DASHBOARD AND ANALYTICS METHODS
    # ==========================================

    async def get_saas_billing_dashboard_metrics(self) -> Dict[str, Any]:
        """Get SaaS billing dashboard metrics"""
        try:
            # Total active subscriptions
            active_subscriptions_query = select(func.count(CompanySubscription.id)).where(
                CompanySubscription.status == "active"
            )
            active_subscriptions_result = await self.db.execute(active_subscriptions_query)
            active_subscriptions = active_subscriptions_result.scalar() or 0

            # Total pending invoices
            pending_query = select(
                func.count(ProTeamCareInvoice.id),
                func.coalesce(func.sum(ProTeamCareInvoice.amount), 0)
            ).where(ProTeamCareInvoice.status.in_(["pending", "sent"]))

            pending_result = await self.db.execute(pending_query)
            pending_count, pending_amount = pending_result.first() or (0, Decimal("0"))

            # Total overdue invoices
            overdue_query = select(
                func.count(ProTeamCareInvoice.id),
                func.coalesce(func.sum(ProTeamCareInvoice.amount), 0)
            ).where(
                and_(
                    ProTeamCareInvoice.due_date < date.today(),
                    ProTeamCareInvoice.status.in_(["pending", "sent"])
                )
            )
            overdue_result = await self.db.execute(overdue_query)
            overdue_count, overdue_amount = overdue_result.first() or (0, Decimal("0"))

            # Current month metrics
            current_month_start = date.today().replace(day=1)
            next_month = (current_month_start.replace(month=current_month_start.month + 1)
                         if current_month_start.month < 12
                         else current_month_start.replace(year=current_month_start.year + 1, month=1))

            # Paid this month
            paid_this_month_query = select(func.coalesce(func.sum(ProTeamCareInvoice.amount), 0)).where(
                and_(
                    ProTeamCareInvoice.status == "paid",
                    ProTeamCareInvoice.paid_at >= current_month_start,
                    ProTeamCareInvoice.paid_at < next_month
                )
            )
            paid_this_month_result = await self.db.execute(paid_this_month_query)
            paid_this_month = paid_this_month_result.scalar() or Decimal("0")

            # Expected this month (created this month)
            expected_this_month_query = select(func.coalesce(func.sum(ProTeamCareInvoice.amount), 0)).where(
                and_(
                    ProTeamCareInvoice.billing_period_start >= current_month_start,
                    ProTeamCareInvoice.billing_period_start < next_month
                )
            )
            expected_this_month_result = await self.db.execute(expected_this_month_query)
            expected_this_month = expected_this_month_result.scalar() or Decimal("0")

            # Collection rate
            collection_rate = (
                (paid_this_month / expected_this_month * 100)
                if expected_this_month > 0
                else Decimal("0")
            )

            # Total establishments count (for MRR calculation)
            establishments_query = select(func.count(Establishments.id)).where(
                Establishments.status == "active"
            )
            establishments_result = await self.db.execute(establishments_query)
            total_establishments = establishments_result.scalar() or 0

            return {
                "total_active_subscriptions": active_subscriptions,
                "total_establishments": total_establishments,
                "total_pending_invoices": pending_count,
                "total_pending_amount": pending_amount,
                "total_overdue_invoices": overdue_count,
                "total_overdue_amount": overdue_amount,
                "total_paid_this_month": paid_this_month,
                "total_expected_this_month": expected_this_month,
                "collection_rate_percentage": collection_rate.quantize(Decimal("0.01")),
            }

        except Exception as e:
            logger.error("Error getting SaaS billing dashboard metrics", error=str(e))
            raise

    async def calculate_subscription_amount(self, subscription_id: int) -> Decimal:
        """Calculate amount for a subscription based on active establishments"""
        try:
            subscription = await self.get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            # Count active establishments for the company
            establishments_query = select(func.count(Establishments.id)).where(
                and_(
                    Establishments.company_id == subscription.company_id,
                    Establishments.status == "active"
                )
            )
            establishments_result = await self.db.execute(establishments_query)
            establishments_count = establishments_result.scalar() or 1  # Minimum 1

            # Calculate amount based on plan
            base_amount = subscription.plan.monthly_price
            total_amount = base_amount * establishments_count

            # Apply volume discounts
            if establishments_count >= 10:
                total_amount *= Decimal("0.85")  # 15% discount
            elif establishments_count >= 5:
                total_amount *= Decimal("0.90")  # 10% discount

            logger.info(
                "Calculated subscription amount",
                subscription_id=subscription_id,
                establishments_count=establishments_count,
                base_amount=base_amount,
                total_amount=total_amount
            )

            return total_amount.quantize(Decimal("0.01"))

        except Exception as e:
            logger.error("Error calculating subscription amount", error=str(e), subscription_id=subscription_id)
            raise

    async def get_upcoming_saas_billings(self, days_ahead: int = 30) -> List[CompanySubscription]:
        """Get upcoming SaaS billing subscriptions"""
        try:
            cutoff_date = date.today() + timedelta(days=days_ahead)
            current_date = date.today()

            # Get subscriptions that need billing
            query = (
                select(CompanySubscription)
                .options(
                    joinedload(CompanySubscription.company),
                    joinedload(CompanySubscription.plan)
                )
                .where(
                    and_(
                        CompanySubscription.status == "active",
                        or_(
                            # Next billing date is the billing_day of current month
                            func.date(func.concat(
                                func.extract('year', current_date), '-',
                                func.extract('month', current_date), '-',
                                CompanySubscription.billing_day
                            )) <= cutoff_date,
                            # Or billing_day already passed this month (need next month)
                            and_(
                                CompanySubscription.billing_day < func.extract('day', current_date),
                                func.date(func.concat(
                                    func.case(
                                        (func.extract('month', current_date) == 12, func.extract('year', current_date) + 1),
                                        else_=func.extract('year', current_date)
                                    ), '-',
                                    func.case(
                                        (func.extract('month', current_date) == 12, 1),
                                        else_=func.extract('month', current_date) + 1
                                    ), '-',
                                    CompanySubscription.billing_day
                                )) <= cutoff_date
                            )
                        )
                    )
                )
                .order_by(CompanySubscription.billing_day)
            )

            result = await self.db.execute(query)
            upcoming_subscriptions = result.unique().scalars().all()

            return upcoming_subscriptions

        except Exception as e:
            logger.error("Error getting upcoming SaaS billings", error=str(e))
            raise

    # ==========================================
    # PAGBANK INTEGRATION METHODS
    # ==========================================

    async def update_subscription_payment_method(
        self,
        subscription_id: int,
        payment_method: str,
        pagbank_subscription_id: Optional[str] = None
    ) -> Optional[CompanySubscription]:
        """Update subscription payment method and PagBank data"""
        try:
            update_data = {
                "payment_method": payment_method,
                "updated_at": datetime.utcnow()
            }

            if pagbank_subscription_id:
                update_data["pagbank_subscription_id"] = pagbank_subscription_id

            stmt = (
                update(CompanySubscription)
                .where(CompanySubscription.id == subscription_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated subscription
            subscription = await self.get_subscription_by_id(subscription_id)

            logger.info(
                "Subscription payment method updated successfully",
                subscription_id=subscription_id,
                payment_method=payment_method
            )

            return subscription

        except Exception as e:
            logger.error(
                "Error updating subscription payment method",
                error=str(e),
                subscription_id=subscription_id,
                payment_method=payment_method
            )
            raise

    async def get_subscription_by_pagbank_id(self, pagbank_subscription_id: str) -> Optional[CompanySubscription]:
        """Get subscription by PagBank subscription ID"""
        try:
            query = (
                select(CompanySubscription)
                .options(
                    joinedload(CompanySubscription.company),
                    joinedload(CompanySubscription.plan)
                )
                .where(CompanySubscription.pagbank_subscription_id == pagbank_subscription_id)
            )

            result = await self.db.execute(query)
            subscription = result.unique().scalar_one_or_none()

            if subscription:
                logger.info(
                    "Found subscription by PagBank ID",
                    subscription_id=subscription.id,
                    pagbank_subscription_id=pagbank_subscription_id
                )
            else:
                logger.warning(
                    "Subscription not found for PagBank ID",
                    pagbank_subscription_id=pagbank_subscription_id
                )

            return subscription

        except Exception as e:
            logger.error(
                "Error getting subscription by PagBank ID",
                error=str(e),
                pagbank_subscription_id=pagbank_subscription_id
            )
            raise

    async def get_recurrent_subscriptions(self, include_inactive: bool = False) -> List[CompanySubscription]:
        """Get all recurrent billing subscriptions"""
        try:
            filters = [CompanySubscription.payment_method == "recurrent"]

            if not include_inactive:
                filters.append(CompanySubscription.status == "active")

            query = (
                select(CompanySubscription)
                .options(
                    joinedload(CompanySubscription.company),
                    joinedload(CompanySubscription.plan)
                )
                .where(and_(*filters))
            )

            result = await self.db.execute(query)
            subscriptions = result.unique().scalars().all()

            logger.info(
                "Retrieved recurrent subscriptions",
                count=len(subscriptions)
            )

            return subscriptions

        except Exception as e:
            logger.error("Error getting recurrent subscriptions", error=str(e))
            raise