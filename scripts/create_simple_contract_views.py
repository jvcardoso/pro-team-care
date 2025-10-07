#!/usr/bin/env python3
"""
Script para criar views estratégicas simplificadas para contratos home care
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def create_simple_views():
    print("=== CRIANDO VIEWS ESTRATÉGICAS SIMPLIFICADAS ===")

    try:
        async for db in get_db():
            # 1. CONTRACT BASIC DASHBOARD VIEW
            print("📊 Criando contract_basic_dashboard_view...")
            basic_dashboard_sql = text(
                """
                CREATE OR REPLACE VIEW contract_basic_dashboard_view AS
                SELECT
                    c.id,
                    c.contract_number,
                    c.client_id,
                    cl.name as client_name,
                    p.tax_id as client_tax_id,
                    c.contract_type,
                    c.lives_contracted,
                    c.monthly_value,
                    c.start_date,
                    c.end_date,
                    c.status,

                    -- Status de saúde do contrato
                    CASE
                        WHEN c.status = 'active' AND c.end_date IS NULL THEN 'healthy'
                        WHEN c.status = 'active' AND c.end_date > CURRENT_DATE THEN 'healthy'
                        WHEN c.status = 'active' AND c.end_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_soon'
                        WHEN c.status = 'suspended' THEN 'suspended'
                        WHEN c.status = 'terminated' THEN 'terminated'
                        ELSE 'unknown'
                    END as health_status,

                    -- Dias até o vencimento
                    CASE
                        WHEN c.end_date IS NOT NULL THEN
                            EXTRACT(DAY FROM c.end_date - CURRENT_DATE)
                        ELSE NULL
                    END as days_to_expiry,

                    c.created_at,
                    c.updated_at

                FROM contracts c
                LEFT JOIN clients cl ON c.client_id = cl.id
                LEFT JOIN people p ON cl.person_id = p.id
                WHERE c.deleted_at IS NULL
                ORDER BY c.updated_at DESC;
            """
            )

            await db.execute(basic_dashboard_sql)
            print("✅ contract_basic_dashboard_view criada com sucesso!")

            # 2. SERVICES BASIC VIEW
            print("📈 Criando services_basic_view...")
            services_basic_sql = text(
                """
                CREATE OR REPLACE VIEW services_basic_view AS
                SELECT
                    sc.id as service_id,
                    sc.service_code,
                    sc.service_name,
                    sc.service_category,
                    sc.service_type,
                    sc.default_unit_value,
                    sc.requires_prescription,
                    sc.home_visit_required,
                    sc.is_active,
                    sc.created_at,
                    sc.updated_at

                FROM services_catalog sc
                WHERE sc.deleted_at IS NULL
                ORDER BY sc.service_name;
            """
            )

            await db.execute(services_basic_sql)
            print("✅ services_basic_view criada com sucesso!")

            # 3. CONTRACT SUMMARY VIEW
            print("👥 Criando contract_summary_view...")
            contract_summary_sql = text(
                """
                CREATE OR REPLACE VIEW contract_summary_view AS
                SELECT
                    c.id as contract_id,
                    c.contract_number,
                    c.client_id,
                    cl.name as client_name,
                    p.tax_id as client_tax_id,
                    c.contract_type,
                    c.lives_contracted,
                    c.lives_minimum,
                    c.lives_maximum,
                    c.allows_substitution,
                    c.monthly_value,
                    c.start_date,
                    c.end_date,
                    c.status,

                    -- Duração do contrato em dias
                    CASE
                        WHEN c.end_date IS NOT NULL THEN
                            EXTRACT(DAY FROM c.end_date - c.start_date)
                        ELSE NULL
                    END as contract_duration_days,

                    -- Valor total do contrato (se tiver data de fim)
                    CASE
                        WHEN c.end_date IS NOT NULL AND c.monthly_value IS NOT NULL THEN
                            c.monthly_value * EXTRACT(MONTH FROM AGE(c.end_date, c.start_date))
                        ELSE NULL
                    END as total_contract_value,

                    c.created_at,
                    c.updated_at,
                    c.created_by

                FROM contracts c
                LEFT JOIN clients cl ON c.client_id = cl.id
                LEFT JOIN people p ON cl.person_id = p.id
                WHERE c.deleted_at IS NULL
                ORDER BY c.created_at DESC;
            """
            )

            await db.execute(contract_summary_sql)
            print("✅ contract_summary_view criada com sucesso!")

            # 4. CONTRACTS BY STATUS VIEW
            print("📊 Criando contracts_by_status_view...")
            status_summary_sql = text(
                """
                CREATE OR REPLACE VIEW contracts_by_status_view AS
                SELECT
                    c.status,
                    COUNT(*) as contract_count,
                    SUM(c.lives_contracted) as total_lives_contracted,
                    SUM(COALESCE(c.monthly_value, 0)) as total_monthly_value,
                    AVG(COALESCE(c.monthly_value, 0)) as avg_monthly_value,
                    MIN(c.start_date) as earliest_start_date,
                    MAX(c.start_date) as latest_start_date,
                    COUNT(CASE WHEN c.end_date IS NOT NULL AND c.end_date <= CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_soon_count

                FROM contracts c
                WHERE c.deleted_at IS NULL
                GROUP BY c.status
                ORDER BY contract_count DESC;
            """
            )

            await db.execute(status_summary_sql)
            print("✅ contracts_by_status_view criada com sucesso!")

            # 5. CONTRACTS BY TYPE VIEW
            print("📋 Criando contracts_by_type_view...")
            type_summary_sql = text(
                """
                CREATE OR REPLACE VIEW contracts_by_type_view AS
                SELECT
                    c.contract_type,
                    COUNT(*) as contract_count,
                    SUM(c.lives_contracted) as total_lives_contracted,
                    SUM(COALESCE(c.monthly_value, 0)) as total_monthly_value,
                    AVG(COALESCE(c.monthly_value, 0)) as avg_monthly_value,
                    AVG(c.lives_contracted) as avg_lives_contracted,
                    MIN(COALESCE(c.monthly_value, 0)) as min_monthly_value,
                    MAX(COALESCE(c.monthly_value, 0)) as max_monthly_value

                FROM contracts c
                WHERE c.deleted_at IS NULL
                GROUP BY c.contract_type
                ORDER BY contract_count DESC;
            """
            )

            await db.execute(type_summary_sql)
            print("✅ contracts_by_type_view criada com sucesso!")

            # 6. MONTHLY PERFORMANCE VIEW
            print("📈 Criando monthly_performance_view...")
            monthly_performance_sql = text(
                """
                CREATE OR REPLACE VIEW monthly_performance_view AS
                SELECT
                    DATE_TRUNC('month', c.created_at) as month_year,
                    COUNT(*) as contracts_created,
                    SUM(c.lives_contracted) as lives_contracted,
                    SUM(COALESCE(c.monthly_value, 0)) as total_monthly_value,
                    AVG(COALESCE(c.monthly_value, 0)) as avg_contract_value,
                    COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active_contracts,
                    COUNT(CASE WHEN c.status = 'terminated' THEN 1 END) as terminated_contracts

                FROM contracts c
                WHERE c.deleted_at IS NULL
                  AND c.created_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY DATE_TRUNC('month', c.created_at)
                ORDER BY month_year DESC;
            """
            )

            await db.execute(monthly_performance_sql)
            print("✅ monthly_performance_view criada com sucesso!")

            await db.commit()
            print(f"\n🎉 Todas as views básicas foram criadas com sucesso!")

            # Test the views
            print("\n🧪 Testando as views criadas...")

            test_queries = [
                (
                    "contract_basic_dashboard_view",
                    "SELECT COUNT(*) as total FROM contract_basic_dashboard_view",
                ),
                (
                    "services_basic_view",
                    "SELECT COUNT(*) as total FROM services_basic_view",
                ),
                (
                    "contract_summary_view",
                    "SELECT COUNT(*) as total FROM contract_summary_view",
                ),
                (
                    "contracts_by_status_view",
                    "SELECT COUNT(*) as total FROM contracts_by_status_view",
                ),
                (
                    "contracts_by_type_view",
                    "SELECT COUNT(*) as total FROM contracts_by_type_view",
                ),
                (
                    "monthly_performance_view",
                    "SELECT COUNT(*) as total FROM monthly_performance_view",
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
    await create_simple_views()
    print("\n🎯 Views estratégicas básicas implementadas com sucesso!")
    print("\nViews disponíveis:")
    print("1. 📊 contract_basic_dashboard_view - Dashboard básico de contratos")
    print("2. 📈 services_basic_view - Catálogo básico de serviços")
    print("3. 👥 contract_summary_view - Resumo completo dos contratos")
    print("4. 📊 contracts_by_status_view - Contratos agrupados por status")
    print("5. 📋 contracts_by_type_view - Contratos agrupados por tipo")
    print("6. 📈 monthly_performance_view - Performance mensal de contratos")


if __name__ == "__main__":
    asyncio.run(main())
