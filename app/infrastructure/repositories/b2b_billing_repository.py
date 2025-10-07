"""
Repository para sistema de cobrança B2B Pro Team Care
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.orm.models import (
    Company,
    CompanySubscription,
    ProTeamCareInvoice,
    SubscriptionPlan,
)


class B2BBillingRepository:
    """Repository para operações de cobrança B2B"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ==========================================
    # SUBSCRIPTION PLAN OPERATIONS
    # ==========================================

    async def get_subscription_plans(
        self, active_only: bool = True
    ) -> List[SubscriptionPlan]:
        """Buscar planos de assinatura"""
        query = select(SubscriptionPlan)
        if active_only:
            query = query.where(SubscriptionPlan.is_active == True)
        query = query.order_by(SubscriptionPlan.monthly_price)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_subscription_plan_by_id(
        self, plan_id: int
    ) -> Optional[SubscriptionPlan]:
        """Buscar plano por ID"""
        query = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_subscription_plan(self, plan_data: dict) -> SubscriptionPlan:
        """Criar novo plano de assinatura"""
        try:
            plan = SubscriptionPlan(**plan_data)
            self.db.add(plan)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(plan)
            return plan
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update_subscription_plan(
        self, plan_id: int, update_data: dict
    ) -> Optional[SubscriptionPlan]:
        """Atualizar plano de assinatura"""
        try:
            query = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
            result = await self.db.execute(query)
            plan = result.scalar_one_or_none()

            if plan:
                for key, value in update_data.items():
                    if hasattr(plan, key):
                        setattr(plan, key, value)
                plan.updated_at = datetime.now()
                await self.db.flush()
                await self.db.commit()
                await self.db.refresh(plan)
            return plan
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_subscription_plan(self, plan_id: int) -> bool:
        """Desativar plano de assinatura (soft delete)"""
        try:
            plan = await self.get_subscription_plan_by_id(plan_id)
            if plan:
                plan.is_active = False
                plan.updated_at = datetime.now()
                await self.db.flush()
                await self.db.commit()
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            raise e

    # ==========================================
    # COMPANY SUBSCRIPTION OPERATIONS
    # ==========================================

    async def create_company_subscription(
        self, subscription_data: dict
    ) -> CompanySubscription:
        """Criar nova assinatura para empresa"""
        import structlog

        logger = structlog.get_logger()

        try:
            logger.info("Criando subscription", subscription_data=subscription_data)
            subscription = CompanySubscription(**subscription_data)
            self.db.add(subscription)
            await self.db.flush()
            await self.db.commit()

            # Refresh com eager loading do relacionamento 'plan'
            await self.db.refresh(subscription, attribute_names=["plan"])

            logger.info(
                "Subscription criada com sucesso", subscription_id=subscription.id
            )
            return subscription
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Erro ao criar subscription",
                error=str(e),
                error_type=type(e).__name__,
                subscription_data=subscription_data,
            )
            raise e

    async def get_company_subscription(
        self, company_id: int
    ) -> Optional[CompanySubscription]:
        """Buscar assinatura ativa da empresa"""
        query = (
            select(CompanySubscription)
            .options(selectinload(CompanySubscription.plan))
            .where(
                and_(
                    CompanySubscription.company_id == company_id,
                    CompanySubscription.status == "active",
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_company_subscriptions_batch(
        self, company_ids: List[int]
    ) -> List[Optional[CompanySubscription]]:
        """Buscar assinaturas ativas de múltiplas empresas (bulk operation)"""
        if not company_ids:
            return []

        # Buscar todas as subscriptions ativas das empresas solicitadas
        query = (
            select(CompanySubscription)
            .options(selectinload(CompanySubscription.plan))
            .where(
                and_(
                    CompanySubscription.company_id.in_(company_ids),
                    CompanySubscription.status == "active",
                )
            )
        )
        result = await self.db.execute(query)
        subscriptions = result.scalars().all()

        # Criar mapa company_id -> subscription
        subscription_map = {sub.company_id: sub for sub in subscriptions}

        # Retornar lista ordenada (None para empresas sem subscription)
        return [subscription_map.get(company_id) for company_id in company_ids]

    async def update_company_subscription(
        self, subscription_id: int, update_data: dict
    ) -> Optional[CompanySubscription]:
        """Atualizar assinatura da empresa"""
        try:
            # Buscar subscription com o relacionamento plan já carregado
            query = (
                select(CompanySubscription)
                .options(selectinload(CompanySubscription.plan))
                .where(CompanySubscription.id == subscription_id)
            )
            result = await self.db.execute(query)
            subscription = result.scalar_one_or_none()

            if subscription:
                for key, value in update_data.items():
                    if hasattr(subscription, key):
                        setattr(subscription, key, value)
                subscription.updated_at = datetime.now()

                await self.db.flush()
                await self.db.commit()
                # Remover o refresh por enquanto para debug
                # await self.db.refresh(subscription)

            return subscription
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all_active_subscriptions(self) -> List[CompanySubscription]:
        """Buscar todas as assinaturas ativas"""
        query = (
            select(CompanySubscription)
            .options(
                selectinload(CompanySubscription.plan),
                selectinload(CompanySubscription.company).selectinload(Company.people),
            )
            .where(CompanySubscription.status == "active")
            .order_by(CompanySubscription.billing_day)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ==========================================
    # PRO TEAM CARE INVOICE OPERATIONS
    # ==========================================

    async def create_proteamcare_invoice(
        self, invoice_data: dict
    ) -> ProTeamCareInvoice:
        """Criar nova fatura Pro Team Care"""
        try:
            invoice = ProTeamCareInvoice(**invoice_data)
            self.db.add(invoice)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(invoice)
            return invoice
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_proteamcare_invoice_by_id(
        self, invoice_id: int
    ) -> Optional[ProTeamCareInvoice]:
        """Buscar fatura por ID"""
        query = (
            select(ProTeamCareInvoice)
            .options(
                selectinload(ProTeamCareInvoice.company).selectinload(Company.people),
                selectinload(ProTeamCareInvoice.subscription).selectinload(
                    CompanySubscription.plan
                ),
            )
            .where(ProTeamCareInvoice.id == invoice_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_proteamcare_invoice(
        self, invoice_id: int, update_data: dict
    ) -> Optional[ProTeamCareInvoice]:
        """Atualizar fatura Pro Team Care"""
        try:
            query = select(ProTeamCareInvoice).where(
                ProTeamCareInvoice.id == invoice_id
            )
            result = await self.db.execute(query)
            invoice = result.scalar_one_or_none()

            if invoice:
                for key, value in update_data.items():
                    if hasattr(invoice, key):
                        setattr(invoice, key, value)
                invoice.updated_at = datetime.now()
                await self.db.flush()
                await self.db.commit()
                await self.db.refresh(invoice)

            return invoice
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_company_invoices(
        self, company_id: int, status: Optional[str] = None, limit: int = 50
    ) -> List[ProTeamCareInvoice]:
        """Buscar faturas de uma empresa"""
        query = (
            select(ProTeamCareInvoice)
            .options(
                selectinload(ProTeamCareInvoice.subscription).selectinload(
                    CompanySubscription.plan
                )
            )
            .where(ProTeamCareInvoice.company_id == company_id)
        )

        if status:
            query = query.where(ProTeamCareInvoice.status == status)

        query = query.order_by(desc(ProTeamCareInvoice.created_at)).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_invoices_by_status(
        self, status: str, limit: int = 100
    ) -> List[ProTeamCareInvoice]:
        """Buscar faturas por status"""
        query = (
            select(ProTeamCareInvoice)
            .options(
                selectinload(ProTeamCareInvoice.company).selectinload(Company.people),
                selectinload(ProTeamCareInvoice.subscription).selectinload(
                    CompanySubscription.plan
                ),
            )
            .where(ProTeamCareInvoice.status == status)
            .order_by(desc(ProTeamCareInvoice.due_date))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_overdue_invoices(self) -> List[ProTeamCareInvoice]:
        """Buscar faturas vencidas"""
        today = date.today()
        query = (
            select(ProTeamCareInvoice)
            .options(
                selectinload(ProTeamCareInvoice.company).selectinload(Company.people),
                selectinload(ProTeamCareInvoice.subscription).selectinload(
                    CompanySubscription.plan
                ),
            )
            .where(
                and_(
                    ProTeamCareInvoice.status == "pending",
                    ProTeamCareInvoice.due_date < today,
                )
            )
            .order_by(ProTeamCareInvoice.due_date)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    # ==========================================
    # DASHBOARD METRICS
    # ==========================================

    async def get_billing_metrics(self) -> dict:
        """Buscar métricas de faturamento"""
        # Total de empresas
        total_companies_query = select(func.count(Company.id))
        total_companies_result = await self.db.execute(total_companies_query)
        total_companies = total_companies_result.scalar()

        # Assinaturas ativas
        active_subscriptions_query = select(func.count(CompanySubscription.id)).where(
            CompanySubscription.status == "active"
        )
        active_subscriptions_result = await self.db.execute(active_subscriptions_query)
        active_subscriptions = active_subscriptions_result.scalar()

        # Receita mensal
        monthly_revenue_query = (
            select(func.sum(SubscriptionPlan.monthly_price))
            .select_from(CompanySubscription)
            .join(SubscriptionPlan, CompanySubscription.plan_id == SubscriptionPlan.id)
            .where(CompanySubscription.status == "active")
        )
        monthly_revenue_result = await self.db.execute(monthly_revenue_query)
        monthly_revenue = monthly_revenue_result.scalar() or Decimal("0.00")

        # Faturas pendentes
        pending_invoices_query = select(func.count(ProTeamCareInvoice.id)).where(
            ProTeamCareInvoice.status == "pending"
        )
        pending_invoices_result = await self.db.execute(pending_invoices_query)
        pending_invoices = pending_invoices_result.scalar()

        # Faturas vencidas
        today = date.today()
        overdue_invoices_query = select(func.count(ProTeamCareInvoice.id)).where(
            and_(
                ProTeamCareInvoice.status == "pending",
                ProTeamCareInvoice.due_date < today,
            )
        )
        overdue_invoices_result = await self.db.execute(overdue_invoices_query)
        overdue_invoices = overdue_invoices_result.scalar()

        # Faturas pagas este mês
        first_day_month = date.today().replace(day=1)
        paid_this_month_query = select(func.count(ProTeamCareInvoice.id)).where(
            and_(
                ProTeamCareInvoice.status == "paid",
                ProTeamCareInvoice.paid_at >= first_day_month,
            )
        )
        paid_this_month_result = await self.db.execute(paid_this_month_query)
        paid_this_month = paid_this_month_result.scalar()

        # Receita este mês
        revenue_this_month_query = select(func.sum(ProTeamCareInvoice.amount)).where(
            and_(
                ProTeamCareInvoice.status == "paid",
                ProTeamCareInvoice.paid_at >= first_day_month,
            )
        )
        revenue_this_month_result = await self.db.execute(revenue_this_month_query)
        revenue_this_month = revenue_this_month_result.scalar() or Decimal("0.00")

        return {
            "total_companies": total_companies,
            "active_subscriptions": active_subscriptions,
            "monthly_revenue": monthly_revenue,
            "pending_invoices": pending_invoices,
            "overdue_invoices": overdue_invoices,
            "paid_invoices_this_month": paid_this_month,
            "total_revenue_this_month": revenue_this_month,
        }

    async def get_companies_billing_status(self) -> List[dict]:
        """Buscar status de cobrança das empresas"""
        from app.infrastructure.orm.models import People

        query = (
            select(
                Company.id.label("company_id"),
                People.name.label("company_name"),
                SubscriptionPlan.name.label("plan_name"),
                SubscriptionPlan.monthly_price.label("monthly_amount"),
                CompanySubscription.payment_method,
                CompanySubscription.status,
            )
            .select_from(Company)
            .join(People, Company.person_id == People.id)
            .join(CompanySubscription, Company.id == CompanySubscription.company_id)
            .join(SubscriptionPlan, CompanySubscription.plan_id == SubscriptionPlan.id)
            .where(CompanySubscription.status == "active")
            .order_by(Company.id)
        )

        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result]

    async def get_plan_distribution(self) -> dict:
        """Buscar distribuição de assinaturas por plano"""
        query = (
            select(
                SubscriptionPlan.name.label("plan_name"),
                func.count(CompanySubscription.id).label("count"),
            )
            .select_from(SubscriptionPlan)
            .outerjoin(
                CompanySubscription,
                and_(
                    SubscriptionPlan.id == CompanySubscription.plan_id,
                    CompanySubscription.status == "active",
                ),
            )
            .where(SubscriptionPlan.is_active == True)
            .group_by(SubscriptionPlan.name)
            .order_by(SubscriptionPlan.name)
        )

        result = await self.db.execute(query)
        distribution = {}
        for row in result:
            distribution[row.plan_name] = row.count

        return distribution

    async def generate_invoice_number(
        self, company_id: int, year: int, month: int
    ) -> str:
        """Gerar número da fatura"""
        # Formato: PTC-YYYY-MM-{company_id:04d}-{sequence:03d}
        prefix = f"PTC-{year:04d}-{month:02d}-{company_id:04d}"

        # Buscar última fatura do mesmo período
        query = select(func.count(ProTeamCareInvoice.id)).where(
            and_(
                ProTeamCareInvoice.company_id == company_id,
                func.extract("year", ProTeamCareInvoice.billing_period_start) == year,
                func.extract("month", ProTeamCareInvoice.billing_period_start) == month,
            )
        )
        result = await self.db.execute(query)
        sequence = result.scalar() + 1

        return f"{prefix}-{sequence:03d}"

    async def get_companies_for_billing(
        self, target_day: int
    ) -> List[CompanySubscription]:
        """Buscar empresas para faturamento em um dia específico"""
        query = (
            select(CompanySubscription)
            .options(
                selectinload(CompanySubscription.company).selectinload(Company.people),
                selectinload(CompanySubscription.plan),
            )
            .where(
                and_(
                    CompanySubscription.status == "active",
                    CompanySubscription.billing_day == target_day,
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
