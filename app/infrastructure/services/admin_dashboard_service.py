"""
Serviço para Dashboard Administrativo com dados reais do sistema
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

from sqlalchemy import func, select, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.orm.models import (
    Company,
    Establishments,
    Client,
    User,
    CompanySubscription,
    SubscriptionPlan,
    ProTeamCareInvoice,
    People,
)


class AdminDashboardService:
    """Serviço para buscar métricas do dashboard administrativo"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Buscar todas as métricas do dashboard admin"""

        # 1. Contadores básicos
        summary = await self._get_summary_counts()

        # 2. Métricas de receita
        revenue = await self._get_revenue_metrics()

        # 3. Empresas sem assinatura
        companies_without_subscription = await self._get_companies_without_subscription()

        # 4. Faturas vencidas
        overdue_invoices = await self._get_overdue_invoices()

        # 5. Atividades recentes
        recent_activities = await self._get_recent_activities()

        # 6. Crescimento mensal
        growth = await self._get_monthly_growth()

        return {
            "summary": summary,
            "revenue": revenue,
            "companies_without_subscription": companies_without_subscription,
            "overdue_invoices": overdue_invoices,
            "recent_activities": recent_activities,
            "growth": growth,
            "generated_at": datetime.now(),
        }

    async def _get_summary_counts(self) -> Dict[str, int]:
        """Contadores básicos do sistema"""

        # Total de empresas ativas
        query_companies = select(func.count(Company.id)).where(
            Company.deleted_at.is_(None)
        )
        result = await self.db.execute(query_companies)
        total_companies = result.scalar() or 0

        # Total de estabelecimentos ativos
        query_establishments = select(func.count(Establishments.id)).where(
            Establishments.deleted_at.is_(None)
        )
        result = await self.db.execute(query_establishments)
        total_establishments = result.scalar() or 0

        # Total de clientes ativos
        query_clients = select(func.count(Client.id)).where(
            Client.deleted_at.is_(None)
        )
        result = await self.db.execute(query_clients)
        total_clients = result.scalar() or 0

        # Total de usuários ativos
        query_users = select(func.count(User.id)).where(User.is_active == True)
        result = await self.db.execute(query_users)
        total_users = result.scalar() or 0

        return {
            "total_companies": total_companies,
            "total_establishments": total_establishments,
            "total_clients": total_clients,
            "total_users": total_users,
        }

    async def _get_revenue_metrics(self) -> Dict[str, Any]:
        """Métricas de receita e assinaturas"""

        # MRR (Monthly Recurring Revenue) e assinaturas ativas
        query_mrr = (
            select(
                func.sum(SubscriptionPlan.monthly_price).label("mrr"),
                func.count(CompanySubscription.id).label("active_subscriptions"),
            )
            .select_from(CompanySubscription)
            .join(SubscriptionPlan, CompanySubscription.plan_id == SubscriptionPlan.id)
            .where(CompanySubscription.status == "active")
        )
        result = await self.db.execute(query_mrr)
        row = result.one_or_none()

        mrr = float(row.mrr) if row and row.mrr else 0.0
        active_subscriptions = row.active_subscriptions if row else 0

        # Total de empresas para calcular taxa de conversão
        query_total_companies = select(func.count(Company.id)).where(
            Company.deleted_at.is_(None)
        )
        result = await self.db.execute(query_total_companies)
        total_companies = result.scalar() or 0

        conversion_rate = (
            (active_subscriptions / total_companies * 100) if total_companies > 0 else 0
        )

        # Faturas por status
        query_invoices = (
            select(
                ProTeamCareInvoice.status,
                func.count(ProTeamCareInvoice.id).label("count"),
                func.sum(ProTeamCareInvoice.amount).label("total"),
            )
            .group_by(ProTeamCareInvoice.status)
        )
        result = await self.db.execute(query_invoices)
        invoices_by_status = {}

        for row in result:
            invoices_by_status[row.status] = {
                "count": row.count,
                "total": float(row.total) if row.total else 0.0,
            }

        return {
            "mrr": mrr,
            "active_subscriptions": active_subscriptions,
            "total_companies": total_companies,
            "conversion_rate": round(conversion_rate, 1),
            "pending_invoices": invoices_by_status.get("pending", {"count": 0, "total": 0.0}),
            "paid_invoices": invoices_by_status.get("paid", {"count": 0, "total": 0.0}),
        }

    async def _get_companies_without_subscription(self) -> List[Dict[str, Any]]:
        """Empresas sem assinatura ativa (oportunidades de venda)"""

        query = (
            select(
                Company.id,
                People.name.label("company_name"),
                Company.created_at,
                func.extract("day", func.now() - Company.created_at).label(
                    "days_without_subscription"
                ),
            )
            .select_from(Company)
            .join(People, Company.person_id == People.id)
            .outerjoin(
                CompanySubscription,
                and_(
                    Company.id == CompanySubscription.company_id,
                    CompanySubscription.status == "active",
                ),
            )
            .where(
                and_(
                    CompanySubscription.id.is_(None), Company.deleted_at.is_(None)
                )
            )
            .order_by(desc(Company.created_at))
            .limit(10)
        )

        result = await self.db.execute(query)
        companies = []

        for row in result:
            companies.append(
                {
                    "id": row.id,
                    "name": row.company_name,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "days_without_subscription": int(row.days_without_subscription or 0),
                }
            )

        return companies

    async def _get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Faturas vencidas (atenção financeira)"""

        query = (
            select(
                ProTeamCareInvoice.id,
                ProTeamCareInvoice.company_id,
                People.name.label("company_name"),
                ProTeamCareInvoice.amount,
                ProTeamCareInvoice.due_date,
                ProTeamCareInvoice.invoice_number,
                func.extract("day", func.now() - ProTeamCareInvoice.due_date).label(
                    "days_overdue"
                ),
            )
            .select_from(ProTeamCareInvoice)
            .join(Company, ProTeamCareInvoice.company_id == Company.id)
            .join(People, Company.person_id == People.id)
            .where(
                and_(
                    ProTeamCareInvoice.status == "pending",
                    ProTeamCareInvoice.due_date < func.now(),
                )
            )
            .order_by(ProTeamCareInvoice.due_date.asc())
            .limit(10)
        )

        result = await self.db.execute(query)
        invoices = []

        for row in result:
            invoices.append(
                {
                    "id": row.id,
                    "company_id": row.company_id,
                    "company_name": row.company_name,
                    "invoice_number": row.invoice_number,
                    "amount": float(row.amount),
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "days_overdue": int(row.days_overdue or 0),
                }
            )

        return invoices

    async def _get_recent_activities(self) -> List[Dict[str, Any]]:
        """Atividades recentes do sistema (últimas 10)"""

        activities = []

        # Últimas empresas criadas
        query_companies = (
            select(
                Company.id,
                People.name.label("name"),
                Company.created_at,
            )
            .select_from(Company)
            .join(People, Company.person_id == People.id)
            .where(Company.deleted_at.is_(None))
            .order_by(desc(Company.created_at))
            .limit(5)
        )
        result = await self.db.execute(query_companies)

        for row in result:
            activities.append(
                {
                    "type": "company_created",
                    "icon": "🏢",
                    "title": f"Empresa '{row.name}' criada",
                    "description": f"ID: {row.id}",
                    "timestamp": row.created_at.isoformat() if row.created_at else None,
                }
            )

        # Últimas assinaturas criadas
        query_subscriptions = (
            select(
                CompanySubscription.id,
                CompanySubscription.company_id,
                People.name.label("company_name"),
                CompanySubscription.created_at,
            )
            .select_from(CompanySubscription)
            .join(Company, CompanySubscription.company_id == Company.id)
            .join(People, Company.person_id == People.id)
            .order_by(desc(CompanySubscription.created_at))
            .limit(5)
        )
        result = await self.db.execute(query_subscriptions)

        for row in result:
            activities.append(
                {
                    "type": "subscription_created",
                    "icon": "📋",
                    "title": f"Assinatura criada para '{row.company_name}'",
                    "description": f"Company ID: {row.company_id}",
                    "timestamp": row.created_at.isoformat()
                    if row.created_at
                    else None,
                }
            )

        # Ordenar por timestamp (mais recente primeiro)
        activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)

        return activities[:10]

    async def _get_monthly_growth(self) -> Dict[str, Any]:
        """Crescimento mensal (últimos 30 dias)"""

        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Novas empresas no mês
        query_new_companies = select(func.count(Company.id)).where(
            and_(
                Company.created_at >= thirty_days_ago,
                Company.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query_new_companies)
        new_companies_month = result.scalar() or 0

        # Novas assinaturas no mês
        query_new_subscriptions = select(
            func.count(CompanySubscription.id)
        ).where(CompanySubscription.created_at >= thirty_days_ago)
        result = await self.db.execute(query_new_subscriptions)
        new_subscriptions_month = result.scalar() or 0

        # Novos clientes no mês
        query_new_clients = select(func.count(Client.id)).where(
            and_(
                Client.created_at >= thirty_days_ago,
                Client.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query_new_clients)
        new_clients_month = result.scalar() or 0

        return {
            "new_companies_month": new_companies_month,
            "new_subscriptions_month": new_subscriptions_month,
            "new_clients_month": new_clients_month,
            "period": "últimos 30 dias",
        }
