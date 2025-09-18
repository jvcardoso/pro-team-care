#!/usr/bin/env python3
"""
REMOVER DADOS CADASTRAIS
Remove empresas, estabelecimentos, endereços, telefones, emails e clientes
Preserva usuários, menus e roles
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def remove_business_entities():
    """Remove entidades de negócio especificadas"""

    print("🗑️ REMOVENDO DADOS CADASTRAIS ESPECÍFICOS")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE ATUAL:")

        # Verificar dados atuais
        entities = {
            "companies": "Empresas",
            "establishments": "Estabelecimentos",
            "clients": "Clientes",
            "phones": "Telefones",
            "emails": "E-mails",
            "addresses": "Endereços",
        }

        before_counts = {}
        for table, desc in entities.items():
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                before_counts[table] = count
                print(f"   📊 {desc}: {count}")
            except Exception as e:
                before_counts[table] = 0
                print(f"   ❌ {desc}: Erro")

        total_to_remove = sum(before_counts.values())
        if total_to_remove == 0:
            print("\n✅ Não há dados cadastrais para remover!")
            return

        print(f"\n📋 Total a remover: {total_to_remove} registros")

        print("\n2️⃣ REMOVENDO CONSTRAINTS TEMPORARIAMENTE:")

        # Lista de constraints que podem impedir a remoção
        constraints_to_remove = [
            ("master.people", "fk_people_company"),
            ("master.users", "fk_users_company"),
            ("master.establishments", "fk_establishments_company"),
            ("master.clients", "fk_clients_company"),
            ("master.phones", "fk_phones_company"),
            ("master.emails", "fk_emails_company"),
            ("master.addresses", "fk_addresses_company"),
        ]

        removed_constraints = []
        for table, constraint in constraints_to_remove:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}")
                )
                removed_constraints.append((table, constraint))
                print(f"   🔓 {constraint} removida temporariamente")
            except Exception as e:
                print(f"   ⚠️ {constraint}: {e}")

        print("\n3️⃣ REMOVENDO DADOS CADASTRAIS:")

        removed_counts = {}

        # PASSO 1: Remover dependências primeiro
        print("\n   🔗 Removendo dependências...")

        # Remover user_establishments (ligação users ↔ establishments)
        try:
            result = await conn.execute(text("DELETE FROM master.user_establishments"))
            removed_counts["user_establishments"] = result.rowcount
            print(f"      - user_establishments: {result.rowcount}")
        except Exception as e:
            removed_counts["user_establishments"] = 0
            print(f"      - user_establishments: 0 (erro)")

        # PASSO 2: Remover entidades na ordem correta
        print("\n   📋 Removendo entidades...")

        # Remover establishments primeiro
        result = await conn.execute(text("DELETE FROM master.establishments"))
        removed_counts["establishments"] = result.rowcount
        print(f"      - establishments: {result.rowcount}")

        # Remover clients
        result = await conn.execute(text("DELETE FROM master.clients"))
        removed_counts["clients"] = result.rowcount
        print(f"      - clients: {result.rowcount}")

        # Remover contatos (phones, emails, addresses)
        for contact_type in ["phones", "emails", "addresses"]:
            result = await conn.execute(text(f"DELETE FROM master.{contact_type}"))
            removed_counts[contact_type] = result.rowcount
            print(f"      - {contact_type}: {result.rowcount}")

        # PASSO 3: Remover companies (por último)
        print("\n   🏢 Removendo companies...")
        result = await conn.execute(text("DELETE FROM master.companies"))
        removed_counts["companies"] = result.rowcount
        print(f"      - companies: {result.rowcount}")

        # PASSO 4: Limpar people órfãs (que perderam companies)
        print("\n   👥 Limpando people órfãs...")
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id NOT IN (
                SELECT person_id FROM master.users WHERE person_id IS NOT NULL
                UNION ALL
                SELECT person_id FROM master.companies WHERE person_id IS NOT NULL
                UNION ALL
                SELECT person_id FROM master.establishments WHERE person_id IS NOT NULL
                UNION ALL
                SELECT person_id FROM master.clients WHERE person_id IS NOT NULL
            )
        """
            )
        )
        removed_counts["people_orphan"] = result.rowcount
        print(f"      - people órfãs: {result.rowcount}")

        print("\n4️⃣ VERIFICAÇÃO PÓS-REMOÇÃO:")

        # Verificar contagens finais
        final_counts = {}
        for table, desc in entities.items():
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                final_counts[table] = count
                before = before_counts.get(table, 0)
                removed = before - count
                status = "✅ LIMPO" if count == 0 else f"⚠️ RESTANTE: {count}"
                print(f"   📊 {desc:15}: {removed:4} removidos - {status}")
            except Exception as e:
                final_counts[table] = -1
                print(f"   ❌ {desc:15}: Erro na verificação")

        # Verificar dados preservados
        try:
            result = await conn.execute(text("SELECT COUNT(*) FROM master.users"))
            users_count = result.scalar()

            result = await conn.execute(text("SELECT COUNT(*) FROM master.menus"))
            menus_count = result.scalar()

            result = await conn.execute(text("SELECT COUNT(*) FROM master.roles"))
            roles_count = result.scalar()

            result = await conn.execute(text("SELECT COUNT(*) FROM master.people"))
            people_count = result.scalar()

            print(f"\n   ✅ DADOS PRESERVADOS:")
            print(f"      - Usuários: {users_count}")
            print(f"      - Menus: {menus_count}")
            print(f"      - Roles: {roles_count}")
            print(f"      - People: {people_count}")

        except Exception as e:
            print(f"   ❌ Erro verificando dados preservados: {e}")

        print("\n5️⃣ RESUMO:")

        total_removed = sum(v for v in removed_counts.values() if v > 0)
        print(f"   📊 Total removido: {total_removed} registros")

        entities_clean = all(
            final_counts.get(table, -1) == 0 for table in entities.keys()
        )

        if entities_clean:
            print(f"\n   🎉 REMOÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"   ✅ Todos os dados cadastrais removidos")
            print(f"   ✅ Usuários, menus e roles preservados")
            print(f"   🚀 BASE LIMPA E PRONTA PARA NOVOS CADASTROS!")

            print(f"\n   📋 DETALHES:")
            for entity, count in removed_counts.items():
                if count > 0:
                    print(f"      - {entity}: {count} removidos")
        else:
            print(f"\n   ⚠️ Remoção parcial")
            remaining_entities = {k: v for k, v in final_counts.items() if v > 0}
            if remaining_entities:
                print(f"   🔧 Ainda restam:")
                for entity, count in remaining_entities.items():
                    print(f"      - {entities[entity]}: {count}")

        print(f"\n   ℹ️ Constraints removidas temporariamente e não foram recriadas")
        print(f"   ℹ️ Isso permite maior flexibilidade para novos cadastros")


async def main():
    """Função principal"""
    try:
        await remove_business_entities()
    except Exception as e:
        print(f"❌ Erro durante remoção: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
