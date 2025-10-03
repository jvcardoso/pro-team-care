"""
Serviço para geração automática de relatórios mensais de contratos home care
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.services.contract_dashboard_service import ContractDashboardService

logger = logging.getLogger(__name__)


class AutomatedReportsService:
    """Serviço para geração automática de relatórios mensais"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.dashboard_service = ContractDashboardService(db_session)

    async def generate_monthly_contract_report(
        self,
        contract_id: int,
        year: int,
        month: int,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """Gerar relatório mensal completo para um contrato"""
        try:
            # Definir período do relatório
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            logger.info(f"Gerando relatório mensal para contrato {contract_id} - {year}/{month:02d}")

            # Obter dados executivos do dashboard
            executive_data = await self.dashboard_service.get_executive_dashboard(
                contract_id=contract_id,
                start_date=start_date,
                end_date=end_date
            )

            if not executive_data:
                raise ValueError(f"Contrato {contract_id} não encontrado")

            # Obter métricas detalhadas
            financial_data = await self.dashboard_service.get_financial_metrics(
                contract_id=contract_id,
                start_date=start_date,
                end_date=end_date
            )

            service_data = await self.dashboard_service.get_service_execution_metrics(
                contract_id=contract_id,
                start_date=start_date,
                end_date=end_date
            )

            quality_data = await self.dashboard_service.get_quality_satisfaction_metrics(
                contract_id=contract_id,
                start_date=start_date,
                end_date=end_date
            )

            # Compilar relatório completo
            report = {
                "report_info": {
                    "contract_id": contract_id,
                    "period": {
                        "year": year,
                        "month": month,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "generated_at": datetime.now().isoformat(),
                    "generated_by": "automated_system",
                    "report_type": "monthly_contract"
                },
                "executive_summary": executive_data,
                "financial_metrics": financial_data,
                "service_metrics": service_data,
                "quality_metrics": quality_data,
                "recommendations": await self._generate_recommendations(
                    contract_id, executive_data, financial_data, service_data, quality_data
                )
            }

            # Salvar relatório se solicitado
            if auto_save:
                report_id = await self._save_report(report)
                report["report_info"]["saved_report_id"] = report_id

            logger.info(f"Relatório mensal gerado com sucesso para contrato {contract_id}")
            return report

        except Exception as e:
            logger.error(f"Erro ao gerar relatório mensal: {e}")
            raise

    async def generate_monthly_company_report(
        self,
        company_id: int,
        year: int,
        month: int,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """Gerar relatório mensal consolidado para uma empresa"""
        try:
            # Definir período
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            logger.info(f"Gerando relatório mensal da empresa {company_id} - {year}/{month:02d}")

            # Obter contratos da empresa
            contracts_query = text("""
                SELECT
                    c.id,
                    c.contract_number,
                    c.contract_name,
                    c.status,
                    c.start_date,
                    c.end_date,
                    c.monthly_limit_sessions
                FROM master.home_care_contracts c
                WHERE c.company_id = :company_id
                AND c.status = 'active'
                ORDER BY c.contract_number
            """)

            result = await self.db_session.execute(
                contracts_query,
                {"company_id": company_id}
            )
            contracts = result.fetchall()

            if not contracts:
                raise ValueError(f"Nenhum contrato ativo encontrado para empresa {company_id}")

            # Gerar relatórios individuais para cada contrato
            contract_reports = {}
            consolidated_metrics = {
                "total_contracts": len(contracts),
                "total_executions": 0,
                "total_sessions": 0,
                "total_revenue": 0,
                "average_satisfaction": 0,
                "total_violations": 0
            }

            for contract in contracts:
                try:
                    contract_report = await self.generate_monthly_contract_report(
                        contract_id=contract.id,
                        year=year,
                        month=month,
                        auto_save=False
                    )
                    contract_reports[f"contract_{contract.id}"] = contract_report

                    # Consolidar métricas
                    exec_summary = contract_report.get("executive_summary", {})
                    financial = contract_report.get("financial_metrics", {})

                    consolidated_metrics["total_executions"] += exec_summary.get("total_executions", 0)
                    consolidated_metrics["total_sessions"] += exec_summary.get("total_sessions", 0)
                    consolidated_metrics["total_revenue"] += financial.get("total_billing_amount", 0)

                except Exception as e:
                    logger.error(f"Erro ao gerar relatório do contrato {contract.id}: {e}")
                    contract_reports[f"contract_{contract.id}"] = {"error": str(e)}

            # Calcular métricas médias
            if consolidated_metrics["total_contracts"] > 0:
                # Calcular satisfação média
                satisfaction_scores = []
                for report in contract_reports.values():
                    if isinstance(report, dict) and "quality_metrics" in report:
                        quality = report["quality_metrics"]
                        if "average_satisfaction" in quality:
                            satisfaction_scores.append(quality["average_satisfaction"])

                if satisfaction_scores:
                    consolidated_metrics["average_satisfaction"] = sum(satisfaction_scores) / len(satisfaction_scores)

            # Compilar relatório consolidado
            company_report = {
                "report_info": {
                    "company_id": company_id,
                    "period": {
                        "year": year,
                        "month": month,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "generated_at": datetime.now().isoformat(),
                    "generated_by": "automated_system",
                    "report_type": "monthly_company"
                },
                "consolidated_metrics": consolidated_metrics,
                "contract_reports": contract_reports,
                "company_recommendations": await self._generate_company_recommendations(
                    company_id, consolidated_metrics, contract_reports
                )
            }

            # Salvar relatório se solicitado
            if auto_save:
                report_id = await self._save_report(company_report)
                company_report["report_info"]["saved_report_id"] = report_id

            logger.info(f"Relatório mensal da empresa gerado com sucesso: {company_id}")
            return company_report

        except Exception as e:
            logger.error(f"Erro ao gerar relatório mensal da empresa: {e}")
            raise

    async def schedule_monthly_reports(
        self,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Agendar geração de relatórios mensais para todas as empresas"""
        try:
            if target_date is None:
                # Por padrão, gerar relatório do mês anterior
                today = date.today()
                if today.month == 1:
                    target_date = date(today.year - 1, 12, 1)
                else:
                    target_date = date(today.year, today.month - 1, 1)

            year = target_date.year
            month = target_date.month

            logger.info(f"Iniciando geração automática de relatórios para {year}/{month:02d}")

            # Obter todas as empresas ativas
            companies_query = text("""
                SELECT DISTINCT
                    c.company_id,
                    comp.company_name
                FROM master.home_care_contracts c
                INNER JOIN master.companies comp ON c.company_id = comp.id
                WHERE c.status = 'active'
                ORDER BY comp.company_name
            """)

            result = await self.db_session.execute(companies_query)
            companies = result.fetchall()

            # Gerar relatórios para cada empresa
            generation_results = {
                "target_period": {
                    "year": year,
                    "month": month
                },
                "generated_at": datetime.now().isoformat(),
                "total_companies": len(companies),
                "successful_reports": 0,
                "failed_reports": 0,
                "results": {}
            }

            for company in companies:
                try:
                    company_report = await self.generate_monthly_company_report(
                        company_id=company.company_id,
                        year=year,
                        month=month,
                        auto_save=True
                    )

                    generation_results["results"][f"company_{company.company_id}"] = {
                        "company_name": company.company_name,
                        "status": "success",
                        "report_id": company_report["report_info"].get("saved_report_id")
                    }
                    generation_results["successful_reports"] += 1

                except Exception as e:
                    logger.error(f"Erro ao gerar relatório da empresa {company.company_id}: {e}")
                    generation_results["results"][f"company_{company.company_id}"] = {
                        "company_name": company.company_name,
                        "status": "failed",
                        "error": str(e)
                    }
                    generation_results["failed_reports"] += 1

            logger.info(
                f"Geração de relatórios concluída: {generation_results['successful_reports']} "
                f"sucessos, {generation_results['failed_reports']} falhas"
            )

            return generation_results

        except Exception as e:
            logger.error(f"Erro ao agendar relatórios mensais: {e}")
            raise

    async def get_saved_reports(
        self,
        company_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Listar relatórios salvos com filtros"""
        try:
            # Construir query com filtros
            where_conditions = []
            params = {}

            if company_id:
                where_conditions.append("r.company_id = :company_id")
                params["company_id"] = company_id

            if contract_id:
                where_conditions.append("r.contract_id = :contract_id")
                params["contract_id"] = contract_id

            if year:
                where_conditions.append("r.report_year = :year")
                params["year"] = year

            if month:
                where_conditions.append("r.report_month = :month")
                params["month"] = month

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # Query para contar total
            count_query = text(f"""
                SELECT COUNT(*)
                FROM master.automated_reports r
                {where_clause}
            """)

            count_result = await self.db_session.execute(count_query, params)
            total = count_result.scalar()

            # Query para obter relatórios paginados
            offset = (page - 1) * size
            params.update({"limit": size, "offset": offset})

            reports_query = text(f"""
                SELECT
                    r.id,
                    r.report_type,
                    r.company_id,
                    r.contract_id,
                    r.report_year,
                    r.report_month,
                    r.generated_at,
                    r.report_data,
                    comp.company_name,
                    c.contract_name
                FROM master.automated_reports r
                LEFT JOIN master.companies comp ON r.company_id = comp.id
                LEFT JOIN master.home_care_contracts c ON r.contract_id = c.id
                {where_clause}
                ORDER BY r.generated_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db_session.execute(reports_query, params)
            reports = result.fetchall()

            return {
                "reports": [
                    {
                        "id": report.id,
                        "report_type": report.report_type,
                        "company_id": report.company_id,
                        "company_name": report.company_name,
                        "contract_id": report.contract_id,
                        "contract_name": report.contract_name,
                        "year": report.report_year,
                        "month": report.report_month,
                        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                        "has_data": report.report_data is not None
                    }
                    for report in reports
                ],
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": (total + size - 1) // size
                }
            }

        except Exception as e:
            logger.error(f"Erro ao listar relatórios salvos: {e}")
            raise

    async def _generate_recommendations(
        self,
        contract_id: int,
        executive_data: Dict[str, Any],
        financial_data: Dict[str, Any],
        service_data: Dict[str, Any],
        quality_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gerar recomendações baseadas nos dados do relatório"""
        recommendations = []

        try:
            # Análise de uso de sessões
            usage_percentage = executive_data.get("session_usage_percentage", 0)
            if usage_percentage > 90:
                recommendations.append({
                    "type": "warning",
                    "category": "usage",
                    "message": "Alto uso de sessões (>90%). Considere revisar os limites do contrato.",
                    "priority": "high"
                })
            elif usage_percentage < 50:
                recommendations.append({
                    "type": "info",
                    "category": "usage",
                    "message": "Baixo uso de sessões (<50%). Oportunidade de aumentar utilização.",
                    "priority": "medium"
                })

            # Análise financeira
            billing_efficiency = financial_data.get("billing_efficiency_percentage", 0)
            if billing_efficiency < 80:
                recommendations.append({
                    "type": "alert",
                    "category": "financial",
                    "message": "Baixa eficiência de faturamento (<80%). Revisar processos de cobrança.",
                    "priority": "high"
                })

            # Análise de qualidade
            avg_satisfaction = quality_data.get("average_satisfaction", 0)
            if avg_satisfaction < 4.0:
                recommendations.append({
                    "type": "alert",
                    "category": "quality",
                    "message": "Satisfação abaixo do esperado (<4.0). Implementar plano de melhoria.",
                    "priority": "high"
                })
            elif avg_satisfaction >= 4.5:
                recommendations.append({
                    "type": "success",
                    "category": "quality",
                    "message": "Excelente índice de satisfação (≥4.5). Manter padrão de qualidade.",
                    "priority": "low"
                })

            # Análise de violações
            total_violations = executive_data.get("total_violations", 0)
            if total_violations > 0:
                recommendations.append({
                    "type": "warning",
                    "category": "compliance",
                    "message": f"{total_violations} violação(ões) detectada(s). Revisar processos de controle.",
                    "priority": "medium"
                })

        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            recommendations.append({
                "type": "error",
                "category": "system",
                "message": "Erro ao gerar recomendações automáticas.",
                "priority": "low"
            })

        return recommendations

    async def _generate_company_recommendations(
        self,
        company_id: int,
        consolidated_metrics: Dict[str, Any],
        contract_reports: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gerar recomendações para o nível da empresa"""
        recommendations = []

        try:
            # Análise consolidada
            total_contracts = consolidated_metrics.get("total_contracts", 0)
            avg_satisfaction = consolidated_metrics.get("average_satisfaction", 0)
            total_violations = consolidated_metrics.get("total_violations", 0)

            # Recomendações baseadas na satisfação média
            if avg_satisfaction < 4.0:
                recommendations.append({
                    "type": "alert",
                    "category": "quality",
                    "message": f"Satisfação média da empresa baixa ({avg_satisfaction:.2f}). Programa de melhoria necessário.",
                    "priority": "high"
                })

            # Análise de contratos com problemas
            problematic_contracts = 0
            for contract_key, report in contract_reports.items():
                if isinstance(report, dict) and "error" not in report:
                    quality = report.get("quality_metrics", {})
                    if quality.get("average_satisfaction", 5) < 4.0:
                        problematic_contracts += 1

            if problematic_contracts > 0:
                percentage = (problematic_contracts / total_contracts) * 100
                recommendations.append({
                    "type": "warning",
                    "category": "performance",
                    "message": f"{problematic_contracts} de {total_contracts} contratos ({percentage:.1f}%) com indicadores abaixo do esperado.",
                    "priority": "medium"
                })

        except Exception as e:
            logger.error(f"Erro ao gerar recomendações da empresa: {e}")

        return recommendations

    async def _save_report(self, report_data: Dict[str, Any]) -> int:
        """Salvar relatório no banco de dados"""
        try:
            report_info = report_data["report_info"]

            # Inserir relatório na tabela
            insert_query = text("""
                INSERT INTO master.automated_reports (
                    report_type,
                    company_id,
                    contract_id,
                    report_year,
                    report_month,
                    generated_at,
                    report_data,
                    created_at
                ) VALUES (
                    :report_type,
                    :company_id,
                    :contract_id,
                    :report_year,
                    :report_month,
                    :generated_at,
                    :report_data,
                    NOW()
                ) RETURNING id
            """)

            result = await self.db_session.execute(
                insert_query,
                {
                    "report_type": report_info["report_type"],
                    "company_id": report_info.get("company_id"),
                    "contract_id": report_info.get("contract_id"),
                    "report_year": report_info["period"]["year"],
                    "report_month": report_info["period"]["month"],
                    "generated_at": datetime.fromisoformat(report_info["generated_at"]),
                    "report_data": report_data
                }
            )

            report_id = result.scalar()
            await self.db_session.commit()

            logger.info(f"Relatório salvo com ID: {report_id}")
            return report_id

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Erro ao salvar relatório: {e}")
            raise