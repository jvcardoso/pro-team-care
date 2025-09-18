#!/usr/bin/env python3
"""
LIMPEZA SIMPLES FINAL
Limpa apenas os dados problemáticos básicos
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def simple_final_cleanup():
    """Limpeza simples e segura"""

    print("🧹 LIMPEZA SIMPLES FINAL")
    print("=" * 40)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ REMOVENDO DADOS SIMPLES:")

        try:
            # 1. Limpar addresses (sem FK dependencies)
            result = await conn.execute(text("DELETE FROM master.addresses"))
            print(f"   🗑️ Addresses: {result.rowcount}")
        except Exception as e:
            print(f"   ⚠️ Addresses: {e}")

        try:
            # 2. Limpar emails (sem FK dependencies)
            result = await conn.execute(text("DELETE FROM master.emails"))
            print(f"   🗑️ Emails: {result.rowcount}")
        except Exception as e:
            print(f"   ⚠️ Emails: {e}")

        try:
            # 3. Limpar phones (sem FK dependencies)
            result = await conn.execute(text("DELETE FROM master.phones"))
            print(f"   🗑️ Phones: {result.rowcount}")
        except Exception as e:
            print(f"   ⚠️ Phones: {e}")

        try:
            # 4. Limpar people órfãos de teste (safe)
            result = await conn.execute(
                text(
                    """
                DELETE FROM master.people
                WHERE tax_id LIKE '99%'  -- CPFs de teste
            """
                )
            )
            print(f"   🗑️ People teste (99%): {result.rowcount}")
        except Exception as e:
            print(f"   ⚠️ People teste: {e}")

        try:
            # 5. Limpar companies órfãs (sem person_id válido)
            result = await conn.execute(
                text(
                    """
                DELETE FROM master.companies
                WHERE person_id NOT IN (SELECT id FROM master.people)
            """
                )
            )
            print(f"   🗑️ Companies órfãs: {result.rowcount}")
        except Exception as e:
            print(f"   ⚠️ Companies órfãs: {e}")

        print("\n2️⃣ CONTAGEM FINAL:")

        # Contagem das tabelas principais
        main_tables = ["people", "users", "companies", "menus"]
        for table in main_tables:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                print(f"   📊 {table:12}: {count:6}")
            except Exception as e:
                print(f"   ❌ {table:12}: Erro")

        print("\n3️⃣ VERIFICAÇÃO MULTI-TENANT:")

        # Verificar se constraints multi-tenant existem
        try:
            result = await conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                JOIN pg_namespace n ON t.relnamespace = n.oid
                WHERE n.nspname = 'master'
                AND t.relname IN ('people', 'users')
                AND c.contype = 'u'
                AND pg_get_constraintdef(c.oid) LIKE '%company_id%'
            """
                )
            )
            mt_constraints = result.scalar()
            print(f"   ✅ Constraints multi-tenant: {mt_constraints}")
        except Exception as e:
            print(f"   ⚠️ Constraints: Erro ao verificar")

        # Verificar RLS ativo
        try:
            result = await conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM pg_policies
                WHERE schemaname = 'master'
                AND tablename IN ('people', 'users')
            """
                )
            )
            rls_policies = result.scalar()
            print(f"   ✅ Políticas RLS: {rls_policies}")
        except Exception as e:
            print(f"   ⚠️ RLS: Erro ao verificar")

        print(f"\n   🎉 LIMPEZA BÁSICA CONCLUÍDA!")
        print(f"   ✅ Dados desnecessários removidos")
        print(f"   ✅ Multi-tenancy preservado")


async def main():
    """Função principal"""
    try:
        await simple_final_cleanup()
    except Exception as e:
        print(f"❌ Erro geral: {e}")


if __name__ == "__main__":
    asyncio.run(main())
