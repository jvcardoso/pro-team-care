#!/usr/bin/env python3
"""
LIMPEZA COMPLETA DE EMPRESAS E RELACIONAMENTOS
Remove todas as empresas e seus relacionamentos respeitando foreign keys
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def cleanup_all_companies():
    """Remover todas as empresas e relacionamentos de forma segura"""

    print("🗑️ LIMPEZA COMPLETA DE EMPRESAS")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE ATUAL:")

        # Contar empresas
        result = await conn.execute(text("SELECT COUNT(*) FROM master.companies"))
        companies_count = result.scalar()
        print(f"   📊 Empresas: {companies_count}")

        # Contar relacionamentos
        tables_to_check = [
            "users",
            "establishments",
            "clients",
            "phones",
            "emails",
            "addresses",
        ]

        for table in tables_to_check:
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                print(f"   📊 {table:15}: {count:6}")
            except Exception as e:
                print(f"   ❌ {table:15}: Erro - {e}")

        if companies_count == 0:
            print("\n✅ Não há empresas para remover!")
            return

        # Confirmar limpeza
        print(f"\n⚠️  ATENÇÃO: Será removido:")
        print(f"   - {companies_count} empresas")
        print(f"   - Todos os relacionamentos (users, establishments, clients, etc.)")
        print(f"   - Todas as pessoas associadas")
        print(f"   - Todos os contatos (phones, emails, addresses)")

        response = input(
            "\n❓ Confirma a remoção COMPLETA? (digite 'CONFIRMO' para prosseguir): "
        )

        if response.upper() != "CONFIRMO":
            print("   ⏹️  Limpeza cancelada pelo usuário")
            return

        print("\n2️⃣ EXECUTANDO LIMPEZA (respeitando foreign keys):")

        # PASSO 1: Remover dependências que referenciam companies
        print("\n   🔗 Removendo dependências de companies...")

        # Remover user_roles (dependem de users)
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_roles
            WHERE user_id IN (SELECT id FROM master.users)
        """
            )
        )
        print(f"      - user_roles: {result.rowcount}")

        # Remover user_sessions (dependem de users)
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_sessions
            WHERE user_id IN (SELECT id FROM master.users)
        """
            )
        )
        print(f"      - user_sessions: {result.rowcount}")

        # Remover user_establishments (dependem de users)
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_establishments
            WHERE user_id IN (SELECT id FROM master.users)
        """
            )
        )
        print(f"      - user_establishments: {result.rowcount}")

        # Remover role_permissions (dependem de users)
        result = await conn.execute(
            text(
                """
            DELETE FROM master.role_permissions
            WHERE granted_by IN (SELECT id FROM master.users)
        """
            )
        )
        print(f"      - role_permissions: {result.rowcount}")

        # PASSO 2: Remover entidades que dependem de companies
        print("\n   📋 Removendo entidades dependentes...")

        # Remover users
        result = await conn.execute(text("DELETE FROM master.users"))
        print(f"      - users: {result.rowcount}")

        # Remover establishments
        result = await conn.execute(text("DELETE FROM master.establishments"))
        print(f"      - establishments: {result.rowcount}")

        # Remover clients
        result = await conn.execute(text("DELETE FROM master.clients"))
        print(f"      - clients: {result.rowcount}")

        # PASSO 3: Remover contatos (phones, emails, addresses)
        print("\n   📞 Removendo contatos...")

        result = await conn.execute(text("DELETE FROM master.phones"))
        print(f"      - phones: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.emails"))
        print(f"      - emails: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.addresses"))
        print(f"      - addresses: {result.rowcount}")

        # PASSO 4: Remover companies
        print("\n   🏢 Removendo companies...")
        result = await conn.execute(text("DELETE FROM master.companies"))
        print(f"      - companies: {result.rowcount}")

        # PASSO 5: Remover people órfãs (que não têm mais companies)
        print("\n   👥 Removendo people órfãs...")
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id NOT IN (SELECT person_id FROM master.companies WHERE person_id IS NOT NULL)
        """
            )
        )
        print(f"      - people órfãs: {result.rowcount}")

        print("\n3️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Verificar se limpeza foi completa
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
                print(f"   ❌ {table:15}: Erro")

        # Verificar integridade
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL
        """
            )
        )
        orphan_people = result.scalar()

        print(f"\n4️⃣ INTEGRIDADE:")
        print(f"   📋 People órfãs restantes: {orphan_people}")

        # Status final
        total_remaining = sum(
            final_counts.get(t, 0)
            for t in ["companies", "users", "establishments", "clients"]
        )

        if total_remaining == 0:
            print(f"\n   🎉 LIMPEZA COMPLETA REALIZADA COM SUCESSO!")
            print(f"   ✅ Todas as empresas e relacionamentos foram removidos")
            print(f"   ✅ Base de dados limpa e pronta para novos dados")
            print(f"\n   📊 RESUMO:")
            print(f"      - Companies: 0")
            print(f"      - Users: 0")
            print(f"      - Establishments: 0")
            print(f"      - Clients: 0")
            print(f"      - Contatos: 0")
            if orphan_people == 0:
                print(f"      - People órfãs: 0 ✅")
            else:
                print(f"      - People órfãs: {orphan_people} ⚠️")
        else:
            print(f"\n   ⚠️  Limpeza com ressalvas")
            print(f"   🔧 Verificar registros restantes: {total_remaining}")


async def main():
    """Função principal"""
    try:
        await cleanup_all_companies()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
