#!/usr/bin/env python3
"""
LIMPEZA AUTOMÁTICA DE TODAS AS EMPRESAS
Remove automaticamente todas as empresas e relacionamentos (SEM CONFIRMAÇÃO)
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def cleanup_all_companies_auto():
    """Remover todas as empresas automaticamente"""

    print("🗑️ LIMPEZA AUTOMÁTICA DE TODAS AS EMPRESAS")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE ATUAL:")

        # Contar empresas
        result = await conn.execute(text("SELECT COUNT(*) FROM master.companies"))
        companies_count = result.scalar()
        print(f"   📊 Empresas: {companies_count}")

        if companies_count == 0:
            print("\n✅ Não há empresas para remover!")
            return

        # Contar relacionamentos
        counts_before = {}
        tables_to_check = [
            "users",
            "establishments",
            "clients",
            "phones",
            "emails",
            "addresses",
            "people",
        ]

        for table in tables_to_check:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                counts_before[table] = count
                print(f"   📊 {table:15}: {count:6}")
            except Exception as e:
                counts_before[table] = 0
                print(f"   ❌ {table:15}: Erro")

        print("\n2️⃣ EXECUTANDO LIMPEZA AUTOMÁTICA:")

        removed_counts = {}

        # PASSO 1: Remover dependências que referenciam companies/users
        print("\n   🔗 Removendo dependências...")

        # Remover user_roles
        result = await conn.execute(text("DELETE FROM master.user_roles"))
        removed_counts["user_roles"] = result.rowcount
        print(f"      - user_roles: {result.rowcount}")

        # Remover user_sessions
        result = await conn.execute(text("DELETE FROM master.user_sessions"))
        removed_counts["user_sessions"] = result.rowcount
        print(f"      - user_sessions: {result.rowcount}")

        # Remover user_establishments
        result = await conn.execute(text("DELETE FROM master.user_establishments"))
        removed_counts["user_establishments"] = result.rowcount
        print(f"      - user_establishments: {result.rowcount}")

        # Remover role_permissions
        result = await conn.execute(text("DELETE FROM master.role_permissions"))
        removed_counts["role_permissions"] = result.rowcount
        print(f"      - role_permissions: {result.rowcount}")

        # PASSO 2: Remover entidades principais
        print("\n   📋 Removendo entidades principais...")

        # Remover users
        result = await conn.execute(text("DELETE FROM master.users"))
        removed_counts["users"] = result.rowcount
        print(f"      - users: {result.rowcount}")

        # Remover establishments
        result = await conn.execute(text("DELETE FROM master.establishments"))
        removed_counts["establishments"] = result.rowcount
        print(f"      - establishments: {result.rowcount}")

        # Remover clients
        result = await conn.execute(text("DELETE FROM master.clients"))
        removed_counts["clients"] = result.rowcount
        print(f"      - clients: {result.rowcount}")

        # PASSO 3: Remover contatos
        print("\n   📞 Removendo contatos...")

        result = await conn.execute(text("DELETE FROM master.phones"))
        removed_counts["phones"] = result.rowcount
        print(f"      - phones: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.emails"))
        removed_counts["emails"] = result.rowcount
        print(f"      - emails: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.addresses"))
        removed_counts["addresses"] = result.rowcount
        print(f"      - addresses: {result.rowcount}")

        # PASSO 4: Remover companies
        print("\n   🏢 Removendo companies...")
        result = await conn.execute(text("DELETE FROM master.companies"))
        removed_counts["companies"] = result.rowcount
        print(f"      - companies: {result.rowcount}")

        # PASSO 5: Remover people órfãs
        print("\n   👥 Limpando people órfãs...")
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id NOT IN (
                SELECT person_id FROM master.companies WHERE person_id IS NOT NULL
                UNION
                SELECT person_id FROM master.users WHERE person_id IS NOT NULL
                UNION
                SELECT person_id FROM master.establishments WHERE person_id IS NOT NULL
                UNION
                SELECT person_id FROM master.clients WHERE person_id IS NOT NULL
            )
        """
            )
        )
        removed_counts["people"] = result.rowcount
        print(f"      - people órfãs: {result.rowcount}")

        print("\n3️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Verificar contagens finais
        final_counts = {}
        all_tables = [
            "companies",
            "users",
            "establishments",
            "clients",
            "phones",
            "emails",
            "addresses",
            "people",
        ]

        for table in all_tables:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                final_counts[table] = count
                status = "✅" if count == 0 else "⚠️"
                print(f"   {status} {table:15}: {count:6}")
            except Exception as e:
                final_counts[table] = -1
                print(f"   ❌ {table:15}: Erro")

        print("\n4️⃣ RESUMO DA LIMPEZA:")

        total_removed = sum(removed_counts.values())
        print(f"   📊 Total registros removidos: {total_removed}")

        main_entities_removed = (
            removed_counts.get("companies", 0)
            + removed_counts.get("users", 0)
            + removed_counts.get("establishments", 0)
            + removed_counts.get("clients", 0)
        )

        print(f"\n   📋 DETALHES:")
        print(f"      - Companies removidas: {removed_counts.get('companies', 0)}")
        print(f"      - Users removidos: {removed_counts.get('users', 0)}")
        print(
            f"      - Establishments removidos: {removed_counts.get('establishments', 0)}"
        )
        print(f"      - Clients removidos: {removed_counts.get('clients', 0)}")
        print(f"      - People órfãs removidas: {removed_counts.get('people', 0)}")
        print(
            f"      - Contatos removidos: {removed_counts.get('phones', 0) + removed_counts.get('emails', 0) + removed_counts.get('addresses', 0)}"
        )

        # Status final
        essential_clean = (
            final_counts.get("companies", 0) == 0
            and final_counts.get("users", 0) == 0
            and final_counts.get("establishments", 0) == 0
            and final_counts.get("clients", 0) == 0
        )

        if essential_clean:
            print(f"\n   🎉 LIMPEZA COMPLETA REALIZADA COM SUCESSO!")
            print(f"   ✅ Todas as empresas e relacionamentos removidos")
            print(f"   ✅ Base limpa - apenas menus preservados")
            print(f"\n   🚀 SISTEMA PRONTO PARA NOVOS DADOS!")
        else:
            print(f"\n   ⚠️  Limpeza com ressalvas")
            remaining = sum(
                final_counts.get(t, 0)
                for t in ["companies", "users", "establishments", "clients"]
            )
            print(f"   🔧 Registros restantes: {remaining}")


async def main():
    """Função principal"""
    try:
        await cleanup_all_companies_auto()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
