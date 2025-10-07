"""
Serviço especializado para dashboard executivo de contratos home care
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.orm.models import (
    AlertsLog,
    Contract,
    ContractLive,
    LimitsViolation,
    MedicalAuthorization,
    ServiceExecution,
    ServicesCatalog,
    ServiceUsageTracking,
)


class ContractDashboardService:
    """Serviço para dashboards executivos de contratos"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_executive_dashboard(
        self,
        contract_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Dashboard executivo completo para um contrato específico
        """
        if start_date is None:
            start_date = date.today().replace(day=1)  # Primeiro dia do mês
        if end_date is None:
            end_date = date.today()

        # Executar queries em paralelo
        contract_info = await self._get_contract_overview(contract_id)
        financial_metrics = await self._get_financial_metrics(
            contract_id, start_date, end_date
        )
        service_metrics = await self._get_service_metrics(
            contract_id, start_date, end_date
        )
        quality_metrics = await self._get_quality_metrics(
            contract_id, start_date, end_date
        )
        limits_status = await self._get_limits_status(contract_id)
        alerts_summary = await self._get_alerts_summary(
            contract_id, start_date, end_date
        )
        trends = await self._get_usage_trends(contract_id, start_date, end_date)

        return {
            "contract_info": contract_info,
            "period": {"start_date": start_date, "end_date": end_date},
            "financial_metrics": financial_metrics,
            "service_metrics": service_metrics,
            "quality_metrics": quality_metrics,
            "limits_status": limits_status,
            "alerts_summary": alerts_summary,
            "usage_trends": trends,
            "generated_at": datetime.utcnow(),
        }

    async def _get_contract_overview(self, contract_id: int) -> Dict[str, Any]:
        """Informações básicas do contrato"""
        query = text(
            """
            SELECT
                c.id,
                c.contract_number,
                c.contract_type,
                c.lives_contracted,
                c.lives_minimum,
                c.lives_maximum,
                c.allows_substitution,
                c.start_date,
                c.end_date,
                c.status,
                c.monthly_value,
                c.payment_frequency,
                cl.name as client_name,
                cl.trade_name,
                COUNT(DISTINCT contract_lives.id) as lives_active,
                COUNT(DISTINCT ma.id) as authorizations_count,
                COUNT(DISTINCT se.id) as executions_count
            FROM master.contracts c
            LEFT JOIN master.clients cl ON c.client_id = cl.id
            LEFT JOIN master.contract_lives contract_lives ON c.id = contract_lives.contract_id
            LEFT JOIN master.medical_authorizations ma ON contract_lives.id = ma.contract_life_id
                AND ma.status = 'active'
            LEFT JOIN master.service_executions se ON ma.id = se.authorization_id
                AND se.status = 'completed'
            WHERE c.id = :contract_id
            GROUP BY c.id, cl.name, cl.trade_name
        """
        )

        result = await self.db_session.execute(query, {"contract_id": contract_id})
        row = result.fetchone()

        if not row:
            return {}

        return {
            "contract_id": row.id,
            "contract_number": row.contract_number,
            "contract_type": row.contract_type,
            "client_name": row.client_name or row.trade_name,
            "lives_contracted": row.lives_contracted,
            "lives_minimum": row.lives_minimum,
            "lives_maximum": row.lives_maximum,
            "lives_active": row.lives_active,
            "allows_substitution": row.allows_substitution,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "status": row.status,
            "monthly_value": float(row.monthly_value) if row.monthly_value else 0,
            "payment_frequency": row.payment_frequency,
            "authorizations_active": row.authorizations_count,
            "executions_completed": row.executions_count,
        }

    async def _get_financial_metrics(
        self, contract_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Métricas financeiras do período"""
        query = text(
            """
            SELECT
                COUNT(se.id) as total_executions,
                SUM(se.billing_amount) as total_billed,
                SUM(CASE WHEN se.billing_status = 'approved' THEN se.billing_amount ELSE 0 END) as approved_amount,
                SUM(CASE WHEN se.billing_status = 'paid' THEN se.billing_amount ELSE 0 END) as paid_amount,
                AVG(se.billing_amount) as avg_execution_value,
                COUNT(CASE WHEN se.billing_status = 'pending' THEN 1 END) as pending_approvals,
                COUNT(CASE WHEN se.billing_status = 'rejected' THEN 1 END) as rejected_billings
            FROM master.service_executions se
            JOIN master.medical_authorizations ma ON se.authorization_id = ma.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            WHERE cl.contract_id = :contract_id
            AND se.execution_date BETWEEN :start_date AND :end_date
            AND se.status = 'completed'
        """
        )

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        row = result.fetchone()

        # Calcular margem e eficiência
        contract_query = text(
            """
            SELECT monthly_value FROM master.contracts WHERE id = :contract_id
        """
        )
        contract_result = await self.db_session.execute(
            contract_query, {"contract_id": contract_id}
        )
        contract_row = contract_result.fetchone()
        monthly_value = (
            float(contract_row.monthly_value) if contract_row.monthly_value else 0
        )

        total_billed = float(row.total_billed) if row.total_billed else 0
        approved_amount = float(row.approved_amount) if row.approved_amount else 0
        paid_amount = float(row.paid_amount) if row.paid_amount else 0

        return {
            "total_executions": row.total_executions or 0,
            "total_billed": total_billed,
            "approved_amount": approved_amount,
            "paid_amount": paid_amount,
            "avg_execution_value": (
                float(row.avg_execution_value) if row.avg_execution_value else 0
            ),
            "pending_approvals": row.pending_approvals or 0,
            "rejected_billings": row.rejected_billings or 0,
            "contract_monthly_value": monthly_value,
            "utilization_rate": (
                (total_billed / monthly_value * 100) if monthly_value > 0 else 0
            ),
            "approval_rate": (
                (approved_amount / total_billed * 100) if total_billed > 0 else 0
            ),
            "payment_rate": (
                (paid_amount / approved_amount * 100) if approved_amount > 0 else 0
            ),
        }

    async def _get_service_metrics(
        self, contract_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Métricas de execução de serviços"""
        query = text(
            """
            SELECT
                sc.service_category,
                sc.service_name,
                COUNT(se.id) as executions_count,
                SUM(se.sessions_consumed) as total_sessions,
                AVG(se.satisfaction_rating) as avg_satisfaction,
                COUNT(CASE WHEN se.status = 'no_show' THEN 1 END) as no_shows,
                COUNT(CASE WHEN se.complications IS NOT NULL THEN 1 END) as complications_count,
                AVG(se.duration_minutes) as avg_duration_minutes
            FROM master.service_executions se
            JOIN master.medical_authorizations ma ON se.authorization_id = ma.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            JOIN master.services_catalog sc ON se.service_id = sc.id
            WHERE cl.contract_id = :contract_id
            AND se.execution_date BETWEEN :start_date AND :end_date
            GROUP BY sc.service_category, sc.service_name
            ORDER BY executions_count DESC
        """
        )

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        services = []
        total_executions = 0
        total_sessions = 0
        total_no_shows = 0
        total_complications = 0

        for row in result.fetchall():
            service_data = {
                "service_category": row.service_category,
                "service_name": row.service_name,
                "executions_count": row.executions_count,
                "total_sessions": row.total_sessions,
                "avg_satisfaction": (
                    float(row.avg_satisfaction) if row.avg_satisfaction else 0
                ),
                "no_shows": row.no_shows,
                "complications_count": row.complications_count,
                "avg_duration_minutes": (
                    float(row.avg_duration_minutes) if row.avg_duration_minutes else 0
                ),
            }
            services.append(service_data)

            total_executions += row.executions_count
            total_sessions += row.total_sessions
            total_no_shows += row.no_shows
            total_complications += row.complications_count

        return {
            "services_breakdown": services,
            "summary": {
                "total_executions": total_executions,
                "total_sessions": total_sessions,
                "total_no_shows": total_no_shows,
                "total_complications": total_complications,
                "no_show_rate": (
                    (total_no_shows / total_executions * 100)
                    if total_executions > 0
                    else 0
                ),
                "complication_rate": (
                    (total_complications / total_executions * 100)
                    if total_executions > 0
                    else 0
                ),
            },
        }

    async def _get_quality_metrics(
        self, contract_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Métricas de qualidade e satisfação"""
        query = text(
            """
            SELECT
                AVG(se.satisfaction_rating) as avg_satisfaction,
                COUNT(CASE WHEN se.satisfaction_rating >= 4 THEN 1 END) as high_satisfaction,
                COUNT(CASE WHEN se.satisfaction_rating <= 2 THEN 1 END) as low_satisfaction,
                COUNT(se.satisfaction_rating) as total_ratings,

                -- Métricas de pontualidade (diferença entre horário agendado e início real)
                AVG(EXTRACT(EPOCH FROM (se.start_time - se.start_time))/60) as avg_delay_minutes,

                -- Métricas de checklist
                AVG(
                    CASE
                        WHEN checklist_stats.total_items > 0
                        THEN (checklist_stats.completed_items::float / checklist_stats.total_items * 100)
                        ELSE 0
                    END
                ) as avg_checklist_completion

            FROM master.service_executions se
            JOIN master.medical_authorizations ma ON se.authorization_id = ma.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            LEFT JOIN (
                SELECT
                    ec.execution_id,
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN ec.is_completed THEN 1 END) as completed_items
                FROM master.execution_checklists ec
                GROUP BY ec.execution_id
            ) checklist_stats ON se.id = checklist_stats.execution_id
            WHERE cl.contract_id = :contract_id
            AND se.execution_date BETWEEN :start_date AND :end_date
            AND se.status = 'completed'
        """
        )

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        row = result.fetchone()

        if not row:
            return {}

        total_ratings = row.total_ratings or 0
        avg_satisfaction = float(row.avg_satisfaction) if row.avg_satisfaction else 0
        high_satisfaction = row.high_satisfaction or 0
        low_satisfaction = row.low_satisfaction or 0

        return {
            "satisfaction": {
                "average_rating": avg_satisfaction,
                "total_ratings": total_ratings,
                "high_satisfaction_count": high_satisfaction,
                "low_satisfaction_count": low_satisfaction,
                "high_satisfaction_rate": (
                    (high_satisfaction / total_ratings * 100)
                    if total_ratings > 0
                    else 0
                ),
                "low_satisfaction_rate": (
                    (low_satisfaction / total_ratings * 100) if total_ratings > 0 else 0
                ),
            },
            "operational": {
                "avg_delay_minutes": (
                    float(row.avg_delay_minutes) if row.avg_delay_minutes else 0
                ),
                "avg_checklist_completion": (
                    float(row.avg_checklist_completion)
                    if row.avg_checklist_completion
                    else 0
                ),
            },
        }

    async def _get_limits_status(self, contract_id: int) -> Dict[str, Any]:
        """Status atual dos limites do contrato"""
        query = text(
            """
            SELECT
                COUNT(CASE WHEN lv.violation_type = 'sessions_exceeded' THEN 1 END) as sessions_violations,
                COUNT(CASE WHEN lv.violation_type = 'financial_exceeded' THEN 1 END) as financial_violations,
                COUNT(CASE WHEN lv.violation_type = 'frequency_exceeded' THEN 1 END) as frequency_violations,
                COUNT(lv.id) as total_violations
            FROM master.limits_violations lv
            JOIN master.medical_authorizations ma ON lv.authorization_id = ma.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            WHERE cl.contract_id = :contract_id
            AND lv.detected_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        )

        result = await self.db_session.execute(query, {"contract_id": contract_id})
        row = result.fetchone()

        return {
            "sessions_violations": row.sessions_violations or 0,
            "financial_violations": row.financial_violations or 0,
            "frequency_violations": row.frequency_violations or 0,
            "total_violations": row.total_violations or 0,
            "status": (
                "healthy"
                if (row.total_violations or 0) == 0
                else "warning" if (row.total_violations or 0) < 5 else "critical"
            ),
        }

    async def _get_alerts_summary(
        self, contract_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Resumo de alertas do período"""
        query = text(
            """
            SELECT
                al.severity,
                COUNT(*) as count
            FROM master.alerts_log al
            WHERE al.entity_id = :contract_id
            AND al.created_at BETWEEN :start_date AND :end_date
            GROUP BY al.severity
        """
        )

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        alerts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for row in result.fetchall():
            alerts[row.severity] = row.count

        return {"by_severity": alerts, "total": sum(alerts.values())}

    async def _get_usage_trends(
        self, contract_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Tendências de uso ao longo do tempo"""
        query = text(
            """
            SELECT
                DATE(se.execution_date) as execution_day,
                COUNT(se.id) as executions_count,
                SUM(se.sessions_consumed) as sessions_count,
                SUM(se.billing_amount) as daily_billing
            FROM master.service_executions se
            JOIN master.medical_authorizations ma ON se.authorization_id = ma.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            WHERE cl.contract_id = :contract_id
            AND se.execution_date BETWEEN :start_date AND :end_date
            AND se.status = 'completed'
            GROUP BY DATE(se.execution_date)
            ORDER BY execution_day
        """
        )

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        daily_data = []
        for row in result.fetchall():
            daily_data.append(
                {
                    "date": row.execution_day,
                    "executions": row.executions_count,
                    "sessions": row.sessions_count,
                    "billing": float(row.daily_billing) if row.daily_billing else 0,
                }
            )

        return {
            "daily_data": daily_data,
            "trend_analysis": self._calculate_trends(daily_data),
        }

    def _calculate_trends(self, daily_data: List[Dict]) -> Dict[str, Any]:
        """Calcular tendências baseadas nos dados diários"""
        if len(daily_data) < 2:
            return {"trend": "insufficient_data"}

        # Calcular tendência simples para execuções
        first_half = daily_data[: len(daily_data) // 2]
        second_half = daily_data[len(daily_data) // 2 :]

        avg_first_executions = sum(d["executions"] for d in first_half) / len(
            first_half
        )
        avg_second_executions = sum(d["executions"] for d in second_half) / len(
            second_half
        )

        execution_trend = (
            "increasing"
            if avg_second_executions > avg_first_executions
            else "decreasing"
        )

        return {
            "execution_trend": execution_trend,
            "avg_daily_executions_first_half": avg_first_executions,
            "avg_daily_executions_second_half": avg_second_executions,
            "trend_percentage": (
                (
                    (avg_second_executions - avg_first_executions)
                    / avg_first_executions
                    * 100
                )
                if avg_first_executions > 0
                else 0
            ),
        }
