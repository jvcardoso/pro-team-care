#!/usr/bin/env python3
"""
Script para criar views estratégicas para contratos home care
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def create_strategic_views():
    print("=== CRIANDO VIEWS ESTRATÉGICAS PARA CONTRATOS HOME CARE ===")

    try:
        async for db in get_db():
            # 1. CONTRACT DASHBOARD VIEW
            print("📊 Criando contract_dashboard_view...")
            dashboard_view_sql = text(
                """
                CREATE OR REPLACE VIEW contract_dashboard_view AS
                SELECT
                    c.id,
                    c.contract_number,
                    c.client_id,
                    cl.name as client_name,
                    cl.tax_id as client_tax_id,
                    c.contract_type,
                    c.lives_contracted,
                    c.monthly_value,
                    c.start_date,
                    c.end_date,
                    c.status,

                    -- Contagem de vidas ativas
                    COALESCE(lives_count.active_lives, 0) as active_lives,

                    -- Execuções deste mês
                    COALESCE(monthly_executions.executions_this_month, 0) as executions_this_month,

                    -- Valor total de execuções deste mês
                    COALESCE(monthly_executions.monthly_revenue, 0) as monthly_revenue,

                    -- Próxima execução agendada
                    next_execution.next_execution_date,

                    -- Status de saúde do contrato
                    CASE
                        WHEN c.status = 'active' AND c.end_date IS NULL THEN 'healthy'
                        WHEN c.status = 'active' AND c.end_date > CURRENT_DATE THEN 'healthy'
                        WHEN c.status = 'active' AND c.end_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_soon'
                        WHEN c.status = 'suspended' THEN 'suspended'
                        WHEN c.status = 'terminated' THEN 'terminated'
                        ELSE 'unknown'
                    END as health_status,

                    c.created_at,
                    c.updated_at

                FROM contracts c
                LEFT JOIN clients cl ON c.client_id = cl.id

                -- Subquery para contar vidas ativas
                LEFT JOIN (
                    SELECT
                        contract_id,
                        COUNT(*) as active_lives
                    FROM contract_lives
                    WHERE status = 'active'
                      AND deleted_at IS NULL
                      AND (end_date IS NULL OR end_date > CURRENT_DATE)
                    GROUP BY contract_id
                ) lives_count ON c.id = lives_count.contract_id

                -- Subquery para execuções deste mês
                LEFT JOIN (
                    SELECT
                        cl.contract_id,
                        COUNT(se.id) as executions_this_month,
                        SUM(COALESCE(se.unit_value, sc.default_unit_value, 0)) as monthly_revenue
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id
                        AND se.execution_date >= DATE_TRUNC('month', CURRENT_DATE)
                        AND se.execution_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                        AND se.status = 'completed'
                        AND se.deleted_at IS NULL
                    LEFT JOIN services_catalog sc ON se.service_id = sc.id
                    WHERE cl.deleted_at IS NULL
                    GROUP BY cl.contract_id
                ) monthly_executions ON c.id = monthly_executions.contract_id

                -- Subquery para próxima execução
                LEFT JOIN (
                    SELECT DISTINCT ON (cl.contract_id)
                        cl.contract_id,
                        se.execution_date as next_execution_date
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id
                    WHERE se.execution_date > CURRENT_DATE
                      AND se.status IN ('scheduled', 'in_progress')
                      AND se.deleted_at IS NULL
                      AND cl.deleted_at IS NULL
                    ORDER BY cl.contract_id, se.execution_date ASC
                ) next_execution ON c.id = next_execution.contract_id

                WHERE c.deleted_at IS NULL
                ORDER BY c.updated_at DESC;
            """
            )

            await db.execute(dashboard_view_sql)
            print("✅ contract_dashboard_view criada com sucesso!")

            # 2. SERVICES PERFORMANCE VIEW
            print("📈 Criando services_performance_view...")
            services_performance_sql = text(
                """
                CREATE OR REPLACE VIEW services_performance_view AS
                SELECT
                    sc.id as service_id,
                    sc.service_code,
                    sc.service_name,
                    sc.service_category,
                    sc.service_type,
                    sc.default_unit_value,

                    -- Métricas de performance
                    COUNT(se.id) as total_executions,
                    COUNT(CASE WHEN se.status = 'completed' THEN 1 END) as completed_executions,
                    COUNT(CASE WHEN se.status = 'cancelled' THEN 1 END) as cancelled_executions,
                    COUNT(CASE WHEN se.status = 'no_show' THEN 1 END) as no_show_executions,

                    -- Taxa de sucesso
                    CASE
                        WHEN COUNT(se.id) > 0 THEN
                            ROUND(COUNT(CASE WHEN se.status = 'completed' THEN 1 END)::NUMERIC / COUNT(se.id) * 100, 2)
                        ELSE 0
                    END as success_rate,

                    -- Receita total
                    SUM(CASE WHEN se.status = 'completed' THEN COALESCE(se.unit_value, sc.default_unit_value, 0) ELSE 0 END) as total_revenue,

                    -- Média de valor por execução
                    AVG(CASE WHEN se.status = 'completed' THEN COALESCE(se.unit_value, sc.default_unit_value, 0) END) as avg_execution_value,

                    -- Execuções nos últimos 30 dias
                    COUNT(CASE WHEN se.execution_date >= CURRENT_DATE - INTERVAL '30 days' AND se.status = 'completed' THEN 1 END) as executions_last_30_days,

                    -- Satisfação média do paciente
                    AVG(se.patient_satisfaction) as avg_patient_satisfaction,

                    -- Profissionais únicos que executaram
                    COUNT(DISTINCT se.professional_id) as unique_professionals,

                    sc.is_active,
                    sc.created_at

                FROM services_catalog sc
                LEFT JOIN service_executions se ON sc.id = se.service_id
                    AND se.deleted_at IS NULL
                    AND se.execution_date >= CURRENT_DATE - INTERVAL '1 year'  -- Últimos 12 meses
                WHERE sc.deleted_at IS NULL
                GROUP BY sc.id, sc.service_code, sc.service_name, sc.service_category,
                         sc.service_type, sc.default_unit_value, sc.is_active, sc.created_at
                ORDER BY total_executions DESC, total_revenue DESC;
            """
            )

            await db.execute(services_performance_sql)
            print("✅ services_performance_view criada com sucesso!")

            # 3. CONTRACT LIVES SUMMARY VIEW
            print("👥 Criando contract_lives_summary_view...")
            lives_summary_sql = text(
                """
                CREATE OR REPLACE VIEW contract_lives_summary_view AS
                SELECT
                    c.id as contract_id,
                    c.contract_number,
                    c.client_id,
                    cl.name as client_name,

                    -- Contagem de vidas
                    c.lives_contracted,
                    COUNT(clv.id) as lives_registered,
                    COUNT(CASE WHEN clv.status = 'active' AND (clv.end_date IS NULL OR clv.end_date > CURRENT_DATE) THEN 1 END) as lives_active,
                    COUNT(CASE WHEN clv.is_primary = true THEN 1 END) as primary_lives,

                    -- Ocupação
                    CASE
                        WHEN c.lives_contracted > 0 THEN
                            ROUND(COUNT(CASE WHEN clv.status = 'active' AND (clv.end_date IS NULL OR clv.end_date > CURRENT_DATE) THEN 1 END)::NUMERIC / c.lives_contracted * 100, 2)
                        ELSE 0
                    END as occupancy_rate,

                    -- Vidas disponíveis
                    GREATEST(0, c.lives_contracted - COUNT(CASE WHEN clv.status = 'active' AND (clv.end_date IS NULL OR clv.end_date > CURRENT_DATE) THEN 1 END)) as available_slots,

                    -- Autorizações médicas ativas
                    COUNT(DISTINCT cls.id) as active_authorizations,

                    -- Execuções nos últimos 30 dias
                    COUNT(CASE WHEN se.execution_date >= CURRENT_DATE - INTERVAL '30 days' AND se.status = 'completed' THEN 1 END) as recent_executions,

                    c.status as contract_status,
                    c.start_date,
                    c.end_date

                FROM contracts c
                LEFT JOIN clients cl ON c.client_id = cl.id
                LEFT JOIN contract_lives clv ON c.id = clv.contract_id AND clv.deleted_at IS NULL
                LEFT JOIN contract_life_services cls ON clv.id = cls.contract_life_id
                    AND cls.status = 'active'
                    AND cls.deleted_at IS NULL
                    AND (cls.end_date IS NULL OR cls.end_date > CURRENT_DATE)
                LEFT JOIN service_executions se ON clv.id = se.contract_life_id
                    AND se.deleted_at IS NULL
                WHERE c.deleted_at IS NULL
                GROUP BY c.id, c.contract_number, c.client_id, cl.name, c.lives_contracted, c.status, c.start_date, c.end_date
                ORDER BY c.updated_at DESC;
            """
            )

            await db.execute(lives_summary_sql)
            print("✅ contract_lives_summary_view criada com sucesso!")

            # 4. FINANCIAL SUMMARY VIEW
            print("💰 Criando financial_summary_view...")
            financial_summary_sql = text(
                """
                CREATE OR REPLACE VIEW financial_summary_view AS
                SELECT
                    c.id as contract_id,
                    c.contract_number,
                    c.client_id,
                    cl.name as client_name,
                    c.monthly_value as contracted_monthly_value,

                    -- Receita por período
                    monthly_revenue.current_month_revenue,
                    monthly_revenue.last_month_revenue,
                    quarterly_revenue.current_quarter_revenue,
                    yearly_revenue.current_year_revenue,

                    -- Comparação com valor contratado
                    CASE
                        WHEN c.monthly_value > 0 AND monthly_revenue.current_month_revenue > 0 THEN
                            ROUND(monthly_revenue.current_month_revenue / c.monthly_value * 100, 2)
                        ELSE 0
                    END as monthly_utilization_rate,

                    -- Média de valor por execução
                    execution_stats.avg_execution_value,
                    execution_stats.total_executions_current_month,
                    execution_stats.total_executions_last_month,

                    -- Projeção baseada na tendência
                    CASE
                        WHEN execution_stats.total_executions_current_month > 0 THEN
                            monthly_revenue.current_month_revenue *
                            (DATE_PART('days', DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day') /
                             DATE_PART('day', CURRENT_DATE))
                        ELSE 0
                    END as projected_monthly_revenue,

                    c.status,
                    c.start_date,
                    c.end_date

                FROM contracts c
                LEFT JOIN clients cl ON c.client_id = cl.id

                -- Receita mensal
                LEFT JOIN (
                    SELECT
                        cl.contract_id,
                        SUM(CASE WHEN se.execution_date >= DATE_TRUNC('month', CURRENT_DATE)
                                  AND se.execution_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                                  AND se.status = 'completed'
                                 THEN COALESCE(se.unit_value, sc.default_unit_value, 0) ELSE 0 END) as current_month_revenue,
                        SUM(CASE WHEN se.execution_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                                  AND se.execution_date < DATE_TRUNC('month', CURRENT_DATE)
                                  AND se.status = 'completed'
                                 THEN COALESCE(se.unit_value, sc.default_unit_value, 0) ELSE 0 END) as last_month_revenue
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id AND se.deleted_at IS NULL
                    LEFT JOIN services_catalog sc ON se.service_id = sc.id
                    WHERE cl.deleted_at IS NULL
                    GROUP BY cl.contract_id
                ) monthly_revenue ON c.id = monthly_revenue.contract_id

                -- Receita trimestral
                LEFT JOIN (
                    SELECT
                        cl.contract_id,
                        SUM(CASE WHEN se.execution_date >= DATE_TRUNC('quarter', CURRENT_DATE)
                                  AND se.status = 'completed'
                                 THEN COALESCE(se.unit_value, sc.default_unit_value, 0) ELSE 0 END) as current_quarter_revenue
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id AND se.deleted_at IS NULL
                    LEFT JOIN services_catalog sc ON se.service_id = sc.id
                    WHERE cl.deleted_at IS NULL
                    GROUP BY cl.contract_id
                ) quarterly_revenue ON c.id = quarterly_revenue.contract_id

                -- Receita anual
                LEFT JOIN (
                    SELECT
                        cl.contract_id,
                        SUM(CASE WHEN se.execution_date >= DATE_TRUNC('year', CURRENT_DATE)
                                  AND se.status = 'completed'
                                 THEN COALESCE(se.unit_value, sc.default_unit_value, 0) ELSE 0 END) as current_year_revenue
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id AND se.deleted_at IS NULL
                    LEFT JOIN services_catalog sc ON se.service_id = sc.id
                    WHERE cl.deleted_at IS NULL
                    GROUP BY cl.contract_id
                ) yearly_revenue ON c.id = yearly_revenue.contract_id

                -- Estatísticas de execução
                LEFT JOIN (
                    SELECT
                        cl.contract_id,
                        AVG(CASE WHEN se.status = 'completed' THEN COALESCE(se.unit_value, sc.default_unit_value, 0) END) as avg_execution_value,
                        COUNT(CASE WHEN se.execution_date >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as total_executions_current_month,
                        COUNT(CASE WHEN se.execution_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                                        AND se.execution_date < DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as total_executions_last_month
                    FROM contract_lives cl
                    LEFT JOIN service_executions se ON cl.id = se.contract_life_id AND se.deleted_at IS NULL
                    LEFT JOIN services_catalog sc ON se.service_id = sc.id
                    WHERE cl.deleted_at IS NULL
                    GROUP BY cl.contract_id
                ) execution_stats ON c.id = execution_stats.contract_id

                WHERE c.deleted_at IS NULL
                ORDER BY c.updated_at DESC;
            """
            )

            await db.execute(financial_summary_sql)
            print("✅ financial_summary_view criada com sucesso!")

            await db.commit()
            print(f"\n🎉 Todas as views estratégicas foram criadas com sucesso!")

            # Test the views
            print("\n🧪 Testando as views criadas...")

            test_queries = [
                (
                    "contract_dashboard_view",
                    "SELECT COUNT(*) as total FROM contract_dashboard_view",
                ),
                (
                    "services_performance_view",
                    "SELECT COUNT(*) as total FROM services_performance_view",
                ),
                (
                    "contract_lives_summary_view",
                    "SELECT COUNT(*) as total FROM contract_lives_summary_view",
                ),
                (
                    "financial_summary_view",
                    "SELECT COUNT(*) as total FROM financial_summary_view",
                ),
            ]

            for view_name, query in test_queries:
                try:
                    result = await db.execute(text(query))
                    count = result.fetchone()
                    print(f"✅ {view_name}: {count.total} registros disponíveis")
                except Exception as e:
                    print(f"❌ Erro ao testar {view_name}: {e}")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


async def main():
    await create_strategic_views()
    print("\n🎯 Views estratégicas implementadas com sucesso!")
    print("\nViews disponíveis:")
    print("1. 📊 contract_dashboard_view - Dashboard principal de contratos")
    print("2. 📈 services_performance_view - Performance dos serviços")
    print("3. 👥 contract_lives_summary_view - Resumo de vidas por contrato")
    print("4. 💰 financial_summary_view - Resumo financeiro dos contratos")


if __name__ == "__main__":
    asyncio.run(main())
