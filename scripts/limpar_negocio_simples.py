#!/usr/bin/env python3
"""
LIMPEZA SIMPLES DE DADOS DE NEGÓCIO
Versão simplificada que preserva usuários admin, menus e roles
Remove apenas dados de negócio de forma segura
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def simple_business_cleanup():
    """Limpeza simples de dados de negócio"""

    print("🧹 LIMPEZA SIMPLES DE DADOS DE NEGÓCIO")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE ANTES DA LIMPEZA:")

        # Contar registros atuais
        tables = {
            "users": "Usuários",
            "companies": "Empresas",
            "establishments": "Estabelecimentos",
            "clients": "Clientes",
            "people": "Pessoas",
            "menus": "Menus",
            "roles": "Roles",
        }

        before_counts = {}
        for table, desc in tables.items():
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

        print("\n2️⃣ EXECUTANDO LIMPEZA:")

        removed_counts = {}

        # ETAPA 1: Remover dependências
        print("\n   🔗 Limpando dependências...")

        # Limpar user_roles, user_sessions, user_establishments
        for dep_table in ["user_roles", "user_sessions", "user_establishments"]:
            try:
                result = await conn.execute(text(f"DELETE FROM master.{dep_table}"))
                removed_counts[dep_table] = result.rowcount
                print(f"      - {dep_table}: {result.rowcount}")
            except Exception as e:
                removed_counts[dep_table] = 0
                print(f"      - {dep_table}: 0 (erro)")

        # ETAPA 2: Remover dados de negócio (ordem criteriosa)
        print("\n   📋 Removendo dados de negócio...")

        # Remover establishments primeiro
        result = await conn.execute(text("DELETE FROM master.establishments"))
        removed_counts["establishments"] = result.rowcount
        print(f"      - establishments: {result.rowcount}")

        # Remover clients
        result = await conn.execute(text("DELETE FROM master.clients"))
        removed_counts["clients"] = result.rowcount
        print(f"      - clients: {result.rowcount}")

        # Remover contatos (já devem estar vazios)
        for contact_table in ["phones", "emails", "addresses"]:
            try:
                result = await conn.execute(text(f"DELETE FROM master.{contact_table}"))
                removed_counts[contact_table] = result.rowcount
                print(f"      - {contact_table}: {result.rowcount}")
            except Exception as e:
                removed_counts[contact_table] = 0
                print(f"      - {contact_table}: 0")

        # ETAPA 3: Remover tudo exceto admin, menus e roles
        print("\n   🚀 Limpeza radical (preservando essenciais)...")

        # Temporariamente desabilitar foreign key checks para people->companies
        try:
            await conn.execute(
                text(
                    "ALTER TABLE master.people DROP CONSTRAINT IF EXISTS fk_people_company"
                )
            )
            print("      - Foreign key fk_people_company removida temporariamente")
        except Exception as e:
            print(f"      - Aviso FK: {e}")

        # Remover companies
        result = await conn.execute(text("DELETE FROM master.companies"))
        removed_counts["companies"] = result.rowcount
        print(f"      - companies: {result.rowcount}")

        # Remover usuários que NÃO são admin
        result = await conn.execute(
            text(
                """
            DELETE FROM master.users
            WHERE email_address NOT ILIKE '%admin%'
            AND email_address != 'admin@example.com'
            AND email_address NOT ILIKE '%root%'
        """
            )
        )
        removed_counts["users_normal"] = result.rowcount
        print(f"      - usuários não-admin: {result.rowcount}")

        # Remover people que não são de usuários admin restantes
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id NOT IN (
                SELECT person_id FROM master.users
                WHERE person_id IS NOT NULL
            )
        """
            )
        )
        removed_counts["people_cleanup"] = result.rowcount
        print(f"      - people limpas: {result.rowcount}")

        # Recriar a foreign key se necessário (opcional - pode funcionar sem)
        try:
            await conn.execute(
                text(
                    """
                ALTER TABLE master.people
                ADD CONSTRAINT fk_people_company
                FOREIGN KEY (company_id) REFERENCES master.companies(id)
            """
                )
            )
            print("      - Foreign key fk_people_company recriada")
        except Exception as e:
            print(f"      - FK não recriada (pode ser OK): {e}")

        print("\n3️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Contar registros finais
        after_counts = {}
        for table, desc in tables.items():
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                after_counts[table] = count
                before = before_counts.get(table, 0)
                diff = before - count
                print(f"   📊 {desc:15}: {count:6} (removidos: {diff})")
            except Exception as e:
                after_counts[table] = 0
                print(f"   ❌ {desc:15}: Erro")

        # Verificar usuários restantes
        try:
            result = await conn.execute(
                text("SELECT id, email_address FROM master.users ORDER BY id")
            )
            remaining_users = result.fetchall()
            print(f"\n   👤 USUÁRIOS PRESERVADOS ({len(remaining_users)}):")
            for user in remaining_users:
                print(f"      - ID {user.id}: {user.email_address}")
        except Exception as e:
            print(f"   ❌ Erro listando usuários: {e}")

        print(f"\n4️⃣ RESUMO:")
        total_removed = sum(removed_counts.values())
        print(f"   📊 Total removido: {total_removed} registros")

        essential_preserved = (
            after_counts.get("users", 0) > 0
            and after_counts.get("menus", 0) > 0
            and after_counts.get("roles", 0) > 0
        )

        business_clean = (
            after_counts.get("companies", 0) == 0
            and after_counts.get("establishments", 0) == 0
            and after_counts.get("clients", 0) == 0
        )

        if essential_preserved and business_clean:
            print(f"\n   🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
            print(f"   ✅ Sistema essencial preservado")
            print(f"   ✅ Dados de negócio limpos")
            print(f"   🚀 PRONTO PARA RECADASTRAR COM MULTI-TENANT!")
        else:
            print(f"\n   ⚠️  Limpeza com ressalvas")
            if not essential_preserved:
                print(f"      🔧 Sistema essencial comprometido")
            if not business_clean:
                print(f"      🔧 Dados de negócio não totalmente limpos")


async def main():
    """Função principal"""
    try:
        await simple_business_cleanup()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
