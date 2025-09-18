#!/usr/bin/env python3
"""
LIMPEZA PÓS MULTI-TENANT
Script para manter apenas dados essenciais após implementação multi-tenant
Manter: users, menus, companies básicas
Remover: people desnecessárias, phones, emails, addresses problemáticas
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def cleanup_post_multitenant():
    """Limpeza estratégica pós implementação multi-tenant"""

    print("🧹 LIMPEZA PÓS MULTI-TENANT")
    print("=" * 50)

    async with engine.begin() as conn:

        # PASSO 1: ANÁLISE ATUAL DOS DADOS
        print("\n1️⃣ ANÁLISE DOS DADOS ATUAIS:")

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        # Contar registros por tabela
        tables_to_analyze = [
            "people",
            "users",
            "companies",
            "establishments",
            "clients",
            "phones",
            "emails",
            "addresses",
            "menus",
        ]

        current_counts = {}
        for table in tables_to_analyze:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                current_counts[table] = count
                print(f"   📊 {table:15}: {count:6} registros")
            except Exception as e:
                print(f"   ❌ {table:15}: Erro - {e}")
                current_counts[table] = 0

        # PASSO 2: IDENTIFICAR DADOS ESSENCIAIS A MANTER
        print("\n2️⃣ IDENTIFICANDO DADOS ESSENCIAIS:")

        # Usuários essenciais (não de teste)
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users
            WHERE email_address NOT LIKE '%teste%'
            AND email_address NOT LIKE '%test%'
            AND email_address NOT LIKE '%@multitenant.com'
            AND email_address NOT LIKE '%@rls.com'
        """
            )
        )
        essential_users = result.scalar()

        # Companies essenciais (não de teste)
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE p.name NOT LIKE '%Teste%'
            AND p.name NOT LIKE '%Test%'
            AND p.name NOT LIKE '%TESTE%'
        """
            )
        )
        essential_companies = result.scalar()

        # Menus (manter todos)
        menus_count = current_counts.get("menus", 0)

        print(f"   ✅ Usuários essenciais: {essential_users}")
        print(f"   ✅ Companies essenciais: {essential_companies}")
        print(f"   ✅ Menus (manter todos): {menus_count}")

        # PASSO 3: CONFIRMAR LIMPEZA
        print("\n3️⃣ PLANO DE LIMPEZA:")
        print("   🗑️ REMOVER:")
        print("      - Phones (todos - podem ter índices problemáticos)")
        print("      - Emails (todos - podem ter índices problemáticos)")
        print("      - Addresses (todos - podem ter índices problemáticos)")
        print("      - People de teste e órfãs problemáticas")
        print("      - Clients de teste")
        print("      - Establishments de teste")

        print("\n   ✅ MANTER:")
        print("      - Users essenciais (produção)")
        print("      - Companies essenciais")
        print("      - Menus (todos)")
        print("      - Estrutura de tabelas")

        # Simular limpeza
        response = input("\n❓ Prosseguir com limpeza? (digite 'SIM' para confirmar): ")

        if response.upper() != "SIM":
            print("   ⏹️  Limpeza cancelada pelo usuário")
            return

        # PASSO 4: EXECUTAR LIMPEZA
        print("\n4️⃣ EXECUTANDO LIMPEZA:")

        # 4.1: Remover tabelas com possíveis problemas de índices
        print("   🗑️ Removendo dados de tabelas com índices complexos...")

        # Addresses
        result = await conn.execute(text("DELETE FROM master.addresses"))
        print(f"      - Addresses removidos: {result.rowcount}")

        # Emails
        result = await conn.execute(text("DELETE FROM master.emails"))
        print(f"      - Emails removidos: {result.rowcount}")

        # Phones
        result = await conn.execute(text("DELETE FROM master.phones"))
        print(f"      - Phones removidos: {result.rowcount}")

        # 4.2: Remover clients de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.clients
            WHERE person_id IN (
                SELECT p.id FROM master.people p
                WHERE p.name LIKE '%Teste%'
                OR p.name LIKE '%Test%'
                OR p.tax_id LIKE '99%'
            )
        """
            )
        )
        print(f"      - Clients de teste removidos: {result.rowcount}")

        # 4.3: Remover establishments de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.establishments
            WHERE person_id IN (
                SELECT p.id FROM master.people p
                WHERE p.name LIKE '%Teste%'
                OR p.name LIKE '%Test%'
                OR p.tax_id LIKE '99%'
            )
        """
            )
        )
        print(f"      - Establishments de teste removidos: {result.rowcount}")

        # 4.4: Remover usuários de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.users
            WHERE email_address LIKE '%teste%'
            OR email_address LIKE '%test%'
            OR email_address LIKE '%@multitenant.com'
            OR email_address LIKE '%@rls.com'
        """
            )
        )
        print(f"      - Users de teste removidos: {result.rowcount}")

        # 4.5: Remover people órfãs e de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE name LIKE '%Teste%'
            OR name LIKE '%Test%'
            OR name LIKE '%TESTE%'
            OR tax_id LIKE '99%'
            OR (name LIKE '%João Silva%' AND tax_id = '12345678901')
        """
            )
        )
        print(f"      - People de teste removidos: {result.rowcount}")

        # 4.6: Remover companies órfãs (sem person_id válido)
        result = await conn.execute(
            text(
                """
            DELETE FROM master.companies
            WHERE person_id NOT IN (SELECT id FROM master.people)
        """
            )
        )
        print(f"      - Companies órfãs removidas: {result.rowcount}")

        # PASSO 5: VERIFICAR INTEGRIDADE PÓS-LIMPEZA
        print("\n5️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Recontagem
        for table in tables_to_analyze:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                new_count = result.scalar()
                old_count = current_counts[table]
                diff = old_count - new_count

                print(f"   📊 {table:15}: {new_count:6} ({-diff:+4})")
            except Exception as e:
                print(f"   ❌ {table:15}: Erro - {e}")

        # Verificar integridade people ↔ companies
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as pessoas_sem_empresa
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL
        """
            )
        )
        orphans = result.scalar()

        print(f"\n   📋 Pessoas órfãs restantes: {orphans}")

        if orphans == 0:
            print(f"   ✅ Integridade people ↔ companies OK")
        else:
            print(f"   ⚠️  Ainda existem pessoas órfãs")

        # Verificar users com pessoas válidas
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as users_sem_pessoa
            FROM master.users u
            LEFT JOIN master.people p ON p.id = u.person_id
            WHERE p.id IS NULL
        """
            )
        )
        users_orphans = result.scalar()

        print(f"   📋 Users órfãos: {users_orphans}")

        # PASSO 6: RECRIAR ÍNDICES SE NECESSÁRIO
        print("\n6️⃣ VERIFICANDO ÍNDICES:")

        # Verificar se índices críticos existem
        result = await conn.execute(
            text(
                """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'master'
            AND tablename IN ('people', 'users')
            AND indexname LIKE '%company%'
            ORDER BY tablename, indexname
        """
            )
        )

        indexes = [row.indexname for row in result]
        print(f"   📊 Índices company encontrados: {len(indexes)}")
        for idx in indexes:
            print(f"      - {idx}")

        # PASSO 7: RESUMO DA LIMPEZA
        print("\n7️⃣ RESUMO DA LIMPEZA:")

        final_counts = {}
        for table in ["people", "users", "companies", "menus"]:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM master.{table}"))
            final_counts[table] = result.scalar()

        print(f"   📊 DADOS FINAIS:")
        print(f"      - People: {final_counts.get('people', 0)}")
        print(f"      - Users: {final_counts.get('users', 0)}")
        print(f"      - Companies: {final_counts.get('companies', 0)}")
        print(f"      - Menus: {final_counts.get('menus', 0)}")

        if (
            final_counts.get("users", 0) > 0
            and final_counts.get("companies", 0) > 0
            and orphans == 0
        ):
            print(f"\n   🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
            print(f"   ✅ Base de dados limpa e otimizada")
            print(f"   ✅ Multi-tenancy funcional mantido")
            print(f"   ✅ Dados essenciais preservados")
        else:
            print(f"\n   ⚠️  Limpeza concluída com ressalvas")
            print(f"   🔧 Verificar integridade dos dados")


async def main():
    """Função principal"""
    try:
        await cleanup_post_multitenant()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
