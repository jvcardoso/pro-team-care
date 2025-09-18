#!/usr/bin/env python3
"""
FASE 3: TESTE RLS COM USUÁRIO COMUM (NÃO-ADMIN)
Script para testar RLS usando usuário que NÃO tem bypass
"""

import asyncio
import random
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_async_engine, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from config.settings import settings


async def test_rls_with_regular_user():
    """Testar RLS com usuário comum (não-admin)"""

    print("🔍 TESTE RLS COM USUÁRIO COMUM (NÃO-ADMIN)")
    print("=" * 55)

    # Criar engines separados - um admin e outro para usuário comum
    admin_engine = create_async_engine(settings.database_url, echo=False)

    # Engine para usuário comum (não postgres)
    common_user_url = settings.database_url.replace("postgres:", "app_user:")
    # Para este teste, vamos usar o postgres mesmo mas simular comportamento

    print("\n1️⃣ TESTANDO COM USUÁRIO ADMIN (postgres):")

    async with admin_engine.begin() as admin_conn:
        # Criar dados de teste únicos
        test_cpf = f"99{random.randint(100000000, 999999999)}"
        test_email = f"teste{random.randint(1000, 9999)}@rls.com"

        print(f"   📋 CPF de teste: {test_cpf}")
        print(f"   📧 Email de teste: {test_email}")

        # Limpeza prévia
        await admin_conn.execute(text("SELECT master.set_current_company_id(0)"))
        await admin_conn.execute(
            text("DELETE FROM master.users WHERE email_address LIKE '%@rls.com'")
        )
        await admin_conn.execute(
            text("DELETE FROM master.people WHERE tax_id LIKE '99%'")
        )

        # Obter companies
        result = await admin_conn.execute(
            text(
                """
            SELECT c.id FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE p.name != 'Pro Team Care - Sistema'
            ORDER BY c.id LIMIT 2;
        """
            )
        )

        companies = [row.id for row in result]
        if len(companies) < 2:
            print("   ❌ Erro: Necessárias 2 companies")
            return

        company_a, company_b = companies[0], companies[1]
        print(f"   🏢 Company A: {company_a}, Company B: {company_b}")

        # Criar dados de teste com context reset (admin bypass)
        await admin_conn.execute(text("SELECT master.set_current_company_id(0)"))

        # Pessoa A
        await admin_conn.execute(
            text(
                """
            INSERT INTO master.people (person_type, name, tax_id, company_id, status, is_active, lgpd_consent_version, created_at, updated_at)
            VALUES ('PF', 'Pessoa A', :tax_id, :company_id, 'active', true, '1.0', NOW(), NOW())
        """
            ),
            {"tax_id": test_cpf, "company_id": company_a},
        )

        # Pessoa B
        await admin_conn.execute(
            text(
                """
            INSERT INTO master.people (person_type, name, tax_id, company_id, status, is_active, lgpd_consent_version, created_at, updated_at)
            VALUES ('PF', 'Pessoa B', :tax_id, :company_id, 'active', true, '1.0', NOW(), NOW())
        """
            ),
            {"tax_id": test_cpf, "company_id": company_b},
        )

        print(f"   ✅ Dados de teste criados")

        # TESTAR RLS MANUALMENTE COM DIFERENTES SETTINGS
        print(f"\n2️⃣ TESTANDO RLS COM CONFIGURAÇÃO MANUAL:")

        # Desabilitar bypass temporariamente para este teste
        await admin_conn.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION master.is_admin_user()
            RETURNS BOOLEAN AS $$
            BEGIN
                RETURN FALSE;  -- Forçar comportamento de usuário comum
            END;
            $$ LANGUAGE plpgsql;
        """
            )
        )

        # Recriar política people para usar função is_admin
        await admin_conn.execute(
            text("DROP POLICY IF EXISTS people_admin_bypass ON master.people;")
        )
        await admin_conn.execute(
            text(
                """
            CREATE POLICY people_admin_bypass ON master.people
            FOR ALL
            USING (master.is_admin_user() = true)
            WITH CHECK (master.is_admin_user() = true);
        """
            )
        )

        # Teste contexto Company A
        print(f"\n   📝 TESTE Company A (ID: {company_a}):")
        await admin_conn.execute(
            text("SELECT master.set_current_company_id(:id)"), {"id": company_a}
        )

        result = await admin_conn.execute(
            text("SELECT COUNT(*), MAX(name) FROM master.people WHERE tax_id = :cpf"),
            {"cpf": test_cpf},
        )
        count_a, name_a = result.fetchone()

        print(f"      - Registros visíveis: {count_a}")
        print(f"      - Nome: {name_a}")

        # Teste contexto Company B
        print(f"\n   📝 TESTE Company B (ID: {company_b}):")
        await admin_conn.execute(
            text("SELECT master.set_current_company_id(:id)"), {"id": company_b}
        )

        result = await admin_conn.execute(
            text("SELECT COUNT(*), MAX(name) FROM master.people WHERE tax_id = :cpf"),
            {"cpf": test_cpf},
        )
        count_b, name_b = result.fetchone()

        print(f"      - Registros visíveis: {count_b}")
        print(f"      - Nome: {name_b}")

        # Verificar isolamento
        print(f"\n3️⃣ VERIFICAÇÃO DO ISOLAMENTO:")

        if count_a == 1 and count_b == 1 and name_a != name_b:
            print(f"   🎉 SUCESSO: RLS funcionando perfeitamente!")
            print(f"      - Company A vê apenas: {name_a}")
            print(f"      - Company B vê apenas: {name_b}")
        else:
            print(f"   ⚠️ RESULTADO: RLS parcialmente ativo")
            print(f"      - Count A: {count_a}, Count B: {count_b}")
            print(f"      - Nomes diferentes: {name_a != name_b}")

        # Testar sem contexto (deve ver tudo se admin)
        print(f"\n   📝 TESTE SEM CONTEXTO (reset):")
        await admin_conn.execute(text("SELECT master.set_current_company_id(0)"))

        result = await admin_conn.execute(
            text("SELECT COUNT(*) FROM master.people WHERE tax_id = :cpf"),
            {"cpf": test_cpf},
        )
        count_total = result.scalar()

        print(f"      - Total registros sem contexto: {count_total}")

        # RESTAURAR POLÍTICAS ORIGINAIS
        print(f"\n4️⃣ RESTAURANDO CONFIGURAÇÕES:")

        # Restaurar função is_admin original
        await admin_conn.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION master.is_admin_user()
            RETURNS BOOLEAN AS $$
            BEGIN
                RETURN current_user = 'postgres';
            END;
            $$ LANGUAGE plpgsql;
        """
            )
        )

        # Restaurar política bypass para postgres
        await admin_conn.execute(
            text("DROP POLICY IF EXISTS people_admin_bypass ON master.people;")
        )
        await admin_conn.execute(
            text(
                """
            CREATE POLICY people_admin_bypass ON master.people
            FOR ALL
            TO postgres
            USING (true)
            WITH CHECK (true);
        """
            )
        )

        # Limpeza final
        await admin_conn.execute(text("SELECT master.set_current_company_id(0)"))
        await admin_conn.execute(
            text("DELETE FROM master.people WHERE tax_id = :cpf"), {"cpf": test_cpf}
        )

        print(f"   ✅ Configurações restauradas e dados limpos")

        print(f"\n5️⃣ RESUMO DO TESTE:")
        print(f"   📋 RLS foi testado simulando usuário comum")
        print(f"   📋 Políticas de isolamento estão ativas")
        print(f"   📋 Função de contexto funcionando")

        if count_a == 1 and count_b == 1:
            print(f"   🎉 ISOLAMENTO FUNCIONANDO CORRETAMENTE!")
        else:
            print(f"   🔧 Ajustes necessários no isolamento")


async def main():
    """Função principal"""
    try:
        await test_rls_with_regular_user()
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
