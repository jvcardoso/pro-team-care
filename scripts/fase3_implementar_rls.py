#!/usr/bin/env python3
"""
FASE 3: IMPLEMENTAR ROW-LEVEL SECURITY (RLS)
Script para implementar isolamento automático a nível de banco de dados
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def implement_rls():
    """Implementar Row-Level Security para isolamento multi-tenant"""

    print("🛡️ FASE 3: IMPLEMENTAR ROW-LEVEL SECURITY (RLS)")
    print("=" * 60)

    async with engine.begin() as conn:

        # PASSO 1: CRIAR FUNÇÃO DE CONTEXTO DE COMPANY
        print("\n1️⃣ CRIANDO FUNÇÃO DE CONTEXTO DE COMPANY:")

        print("   ⏳ Criando função get_current_company_id()...")
        await conn.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION master.get_current_company_id()
            RETURNS INTEGER AS $$
            BEGIN
                -- Buscar company_id da sessão atual
                -- Em produção, isso seria obtido do token JWT ou sessão
                RETURN COALESCE(
                    NULLIF(current_setting('app.current_company_id', true), '')::INTEGER,
                    0  -- Fallback para testes
                );
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
            )
        )
        print("   ✅ Função get_current_company_id() criada")

        print("   ⏳ Criando função set_current_company_id()...")
        await conn.execute(
            text(
                """
            CREATE OR REPLACE FUNCTION master.set_current_company_id(company_id INTEGER)
            RETURNS VOID AS $$
            BEGIN
                -- Definir company_id da sessão atual
                PERFORM set_config('app.current_company_id', company_id::TEXT, false);
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
            )
        )
        print("   ✅ Função set_current_company_id() criada")

        # PASSO 2: IMPLEMENTAR RLS NA TABELA PEOPLE
        print("\n2️⃣ IMPLEMENTANDO RLS NA TABELA PEOPLE:")

        print("   ⏳ Habilitando RLS na tabela people...")
        await conn.execute(text("ALTER TABLE master.people ENABLE ROW LEVEL SECURITY;"))
        print("   ✅ RLS habilitado na tabela people")

        print("   ⏳ Criando política de SELECT para people...")
        await conn.execute(
            text(
                """
            CREATE POLICY people_company_isolation_select ON master.people
            FOR SELECT
            USING (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política SELECT criada para people")

        print("   ⏳ Criando política de INSERT para people...")
        await conn.execute(
            text(
                """
            CREATE POLICY people_company_isolation_insert ON master.people
            FOR INSERT
            WITH CHECK (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política INSERT criada para people")

        print("   ⏳ Criando política de UPDATE para people...")
        await conn.execute(
            text(
                """
            CREATE POLICY people_company_isolation_update ON master.people
            FOR UPDATE
            USING (company_id = master.get_current_company_id())
            WITH CHECK (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política UPDATE criada para people")

        print("   ⏳ Criando política de DELETE para people...")
        await conn.execute(
            text(
                """
            CREATE POLICY people_company_isolation_delete ON master.people
            FOR DELETE
            USING (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política DELETE criada para people")

        # PASSO 3: IMPLEMENTAR RLS NA TABELA USERS
        print("\n3️⃣ IMPLEMENTANDO RLS NA TABELA USERS:")

        print("   ⏳ Habilitando RLS na tabela users...")
        await conn.execute(text("ALTER TABLE master.users ENABLE ROW LEVEL SECURITY;"))
        print("   ✅ RLS habilitado na tabela users")

        print("   ⏳ Criando política de SELECT para users...")
        await conn.execute(
            text(
                """
            CREATE POLICY users_company_isolation_select ON master.users
            FOR SELECT
            USING (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política SELECT criada para users")

        print("   ⏳ Criando política de INSERT para users...")
        await conn.execute(
            text(
                """
            CREATE POLICY users_company_isolation_insert ON master.users
            FOR INSERT
            WITH CHECK (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política INSERT criada para users")

        print("   ⏳ Criando política de UPDATE para users...")
        await conn.execute(
            text(
                """
            CREATE POLICY users_company_isolation_update ON master.users
            FOR UPDATE
            USING (company_id = master.get_current_company_id())
            WITH CHECK (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política UPDATE criada para users")

        print("   ⏳ Criando política de DELETE para users...")
        await conn.execute(
            text(
                """
            CREATE POLICY users_company_isolation_delete ON master.users
            FOR DELETE
            USING (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ Política DELETE criada para users")

        # PASSO 4: CRIAR POLÍTICAS BYPASS PARA SUPERUSER
        print("\n4️⃣ CRIANDO POLÍTICAS BYPASS PARA ADMINISTRAÇÃO:")

        print("   ⏳ Criando política bypass para people (admin)...")
        await conn.execute(
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
        print("   ✅ Política admin bypass criada para people")

        print("   ⏳ Criando política bypass para users (admin)...")
        await conn.execute(
            text(
                """
            CREATE POLICY users_admin_bypass ON master.users
            FOR ALL
            TO postgres
            USING (true)
            WITH CHECK (true);
        """
            )
        )
        print("   ✅ Política admin bypass criada para users")

        # PASSO 5: IMPLEMENTAR RLS EM TABELAS RELACIONADAS
        print("\n5️⃣ IMPLEMENTANDO RLS EM TABELAS RELACIONADAS:")

        # RLS para estabelishments (já tem company_id)
        print("   ⏳ Habilitando RLS na tabela establishments...")
        await conn.execute(
            text("ALTER TABLE master.establishments ENABLE ROW LEVEL SECURITY;")
        )

        await conn.execute(
            text(
                """
            CREATE POLICY establishments_company_isolation ON master.establishments
            FOR ALL
            USING (company_id = master.get_current_company_id())
            WITH CHECK (company_id = master.get_current_company_id());
        """
            )
        )
        print("   ✅ RLS implementado na tabela establishments")

        # RLS para clients (através de establishment)
        print("   ⏳ Habilitando RLS na tabela clients...")
        await conn.execute(
            text("ALTER TABLE master.clients ENABLE ROW LEVEL SECURITY;")
        )

        await conn.execute(
            text(
                """
            CREATE POLICY clients_company_isolation ON master.clients
            FOR ALL
            USING (
                establishment_id IN (
                    SELECT id FROM master.establishments
                    WHERE company_id = master.get_current_company_id()
                )
            )
            WITH CHECK (
                establishment_id IN (
                    SELECT id FROM master.establishments
                    WHERE company_id = master.get_current_company_id()
                )
            );
        """
            )
        )
        print("   ✅ RLS implementado na tabela clients")

        # PASSO 6: TESTAR FUNCIONAMENTO DO RLS
        print("\n6️⃣ TESTANDO FUNCIONAMENTO DO RLS:")

        # Obter duas companies para teste
        result = await conn.execute(
            text(
                """
            SELECT c.id, p.name
            FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE p.name != 'Pro Team Care - Sistema'
            ORDER BY c.id
            LIMIT 2;
        """
            )
        )

        test_companies = list(result)

        if len(test_companies) >= 2:
            company1_id = test_companies[0].id
            company2_id = test_companies[1].id
            company1_name = test_companies[0].name[:20]
            company2_name = test_companies[1].name[:20]

            print(f"   🏢 Testando com companies:")
            print(f"      - Company 1: ID {company1_id} | {company1_name}")
            print(f"      - Company 2: ID {company2_id} | {company2_name}")

            # Teste 1: Definir contexto da company 1
            print(f"\n   📝 TESTE 1: Contexto Company {company1_id}")
            await conn.execute(
                text("SELECT master.set_current_company_id(:company_id);"),
                {"company_id": company1_id},
            )

            result = await conn.execute(text("SELECT COUNT(*) FROM master.people;"))
            people_company1 = result.scalar()
            print(f"      - People visíveis: {people_company1}")

            result = await conn.execute(text("SELECT COUNT(*) FROM master.users;"))
            users_company1 = result.scalar()
            print(f"      - Users visíveis: {users_company1}")

            # Teste 2: Definir contexto da company 2
            print(f"\n   📝 TESTE 2: Contexto Company {company2_id}")
            await conn.execute(
                text("SELECT master.set_current_company_id(:company_id);"),
                {"company_id": company2_id},
            )

            result = await conn.execute(text("SELECT COUNT(*) FROM master.people;"))
            people_company2 = result.scalar()
            print(f"      - People visíveis: {people_company2}")

            result = await conn.execute(text("SELECT COUNT(*) FROM master.users;"))
            users_company2 = result.scalar()
            print(f"      - Users visíveis: {users_company2}")

            # Verificar isolamento
            isolated = (
                people_company1 != people_company2 or users_company1 != users_company2
            )
            print(f"\n      ✅ Isolamento funcionando: {'SIM' if isolated else 'NÃO'}")

            # Resetar contexto
            await conn.execute(text("SELECT master.set_current_company_id(0);"))

        # PASSO 7: VERIFICAR POLÍTICAS CRIADAS
        print("\n7️⃣ VERIFICANDO POLÍTICAS CRIADAS:")

        result = await conn.execute(
            text(
                """
            SELECT
                schemaname,
                tablename,
                policyname,
                cmd,
                permissive
            FROM pg_policies
            WHERE schemaname = 'master'
            AND tablename IN ('people', 'users', 'establishments', 'clients')
            ORDER BY tablename, policyname;
        """
            )
        )

        policies = list(result)
        print(f"   📋 Total de políticas criadas: {len(policies)}")

        tables_with_policies = set()
        for policy in policies:
            if policy.tablename not in tables_with_policies:
                print(f"      - {policy.tablename.upper()}: RLS ativo")
                tables_with_policies.add(policy.tablename)

        # PASSO 8: RESUMO FINAL
        print("\n8️⃣ RESUMO DA IMPLEMENTAÇÃO RLS:")

        expected_tables = {"people", "users", "establishments", "clients"}
        implemented_tables = tables_with_policies

        print(
            f"   📊 Tabelas com RLS: {len(implemented_tables)}/{len(expected_tables)}"
        )

        for table in expected_tables:
            status = "✅ ATIVO" if table in implemented_tables else "❌ FALTANDO"
            print(f"      - {table}: {status}")

        if implemented_tables == expected_tables:
            print(f"\n   🎉 RLS IMPLEMENTADO COM SUCESSO!")
            print(f"   ✅ Isolamento automático ativo em todas as tabelas críticas")
            print(f"   ✅ Funções de contexto criadas")
            print(f"   ✅ Políticas de bypass para admin")
            print(f"   🚀 PRONTO PARA ATUALIZAÇÃO DA APLICAÇÃO")
        else:
            missing = expected_tables - implemented_tables
            print(f"\n   ⚠️  RLS PARCIALMENTE IMPLEMENTADO")
            print(f"   🔧 Faltam tabelas: {missing}")


async def main():
    """Função principal"""
    try:
        await implement_rls()
    except Exception as e:
        print(f"❌ Erro durante implementação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
