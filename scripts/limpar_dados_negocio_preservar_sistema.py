#!/usr/bin/env python3
"""
LIMPEZA DE DADOS DE NEGÓCIO - PRESERVANDO SISTEMA
Remove dados cadastrais (empresas, clientes, etc.) mas preserva:
- 1 usuário ROOT/admin
- Todos os menus
- Todas as roles
- Estrutura do sistema
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def cleanup_business_data_preserve_system():
    """Limpar dados de negócio preservando estrutura do sistema"""

    print("🧹 LIMPEZA DE DADOS DE NEGÓCIO - PRESERVANDO SISTEMA")
    print("=" * 60)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE DO SISTEMA ATUAL:")

        # Verificar usuários (identificar o admin/root)
        result = await conn.execute(
            text(
                """
            SELECT id, email_address,
                   CASE WHEN email_address ILIKE '%admin%'
                        OR email_address ILIKE '%root%'
                        OR email_address = 'admin@example.com'
                   THEN 'ADMIN' ELSE 'NORMAL' END as user_type
            FROM master.users
            ORDER BY id
        """
            )
        )
        users = result.fetchall()

        admin_users = [u for u in users if u.user_type == "ADMIN"]
        normal_users = [u for u in users if u.user_type == "NORMAL"]

        print(f"   👤 Usuários ADMIN/ROOT: {len(admin_users)}")
        for admin in admin_users:
            print(f"      - ID {admin.id}: {admin.email_address} ✅ PRESERVAR")

        print(f"   👥 Usuários NORMAIS: {len(normal_users)}")
        for user in normal_users:
            print(f"      - ID {user.id}: {user.email_address} 🗑️ REMOVER")

        # Contar elementos que serão preservados
        result = await conn.execute(text("SELECT COUNT(*) FROM master.menus"))
        menus_count = result.scalar()

        result = await conn.execute(text("SELECT COUNT(*) FROM master.roles"))
        roles_count = result.scalar()

        print(f"\n   📋 Menus: {menus_count} ✅ PRESERVAR TODOS")
        print(f"   🔐 Roles: {roles_count} ✅ PRESERVAR TODAS")

        # Contar dados de negócio que serão removidos
        business_tables = {
            "companies": "Empresas",
            "establishments": "Estabelecimentos",
            "clients": "Clientes",
            "phones": "Telefones",
            "emails": "E-mails",
            "addresses": "Endereços",
        }

        business_counts = {}
        print(f"\n   🗑️ DADOS DE NEGÓCIO A REMOVER:")
        for table, desc in business_tables.items():
            try:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM master.{table}")
                )
                count = result.scalar()
                business_counts[table] = count
                print(f"      - {desc}: {count}")
            except Exception as e:
                business_counts[table] = 0
                print(f"      - {desc}: 0 (erro: {e})")

        # Verificar people que serão afetadas
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            WHERE p.id IN (SELECT person_id FROM master.companies)
        """
            )
        )
        company_people = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            WHERE p.id NOT IN (
                SELECT person_id FROM master.users WHERE person_id IS NOT NULL
                UNION
                SELECT person_id FROM master.companies WHERE person_id IS NOT NULL
            )
        """
            )
        )
        orphan_people = result.scalar()

        print(f"\n   👥 PESSOAS:")
        print(f"      - Ligadas a empresas: {company_people} 🗑️ REMOVER")
        print(f"      - Órfãs: {orphan_people} 🗑️ REMOVER")
        print(f"      - Ligadas a usuários admin: ✅ PRESERVAR")

        total_to_remove = (
            sum(business_counts.values())
            + company_people
            + orphan_people
            + len(normal_users)
        )

        if len(admin_users) == 0:
            print(f"\n❌ ERRO: Nenhum usuário ADMIN encontrado!")
            print(f"   🔧 Sem usuário admin, o sistema ficará inacessível")
            return

        print(f"\n📊 RESUMO:")
        print(
            f"   ✅ PRESERVAR: {len(admin_users)} admin(s), {menus_count} menus, {roles_count} roles"
        )
        print(f"   🗑️ REMOVER: {total_to_remove} registros de dados de negócio")

        # Executar limpeza
        print(f"\n2️⃣ EXECUTANDO LIMPEZA SELETIVA:")

        removed_counts = {}

        # PASSO 1: Remover dependências de usuários normais
        print(f"\n   🔗 Removendo dependências de usuários normais...")

        if normal_users:
            normal_user_ids = [str(u.id) for u in normal_users]
            user_ids_str = ",".join(normal_user_ids)

            # Remover user_roles de usuários normais
            result = await conn.execute(
                text(
                    f"""
                DELETE FROM master.user_roles
                WHERE user_id IN ({user_ids_str})
            """
                )
            )
            removed_counts["user_roles"] = result.rowcount
            print(f"      - user_roles (normais): {result.rowcount}")

            # Remover user_sessions de usuários normais
            result = await conn.execute(
                text(
                    f"""
                DELETE FROM master.user_sessions
                WHERE user_id IN ({user_ids_str})
            """
                )
            )
            removed_counts["user_sessions"] = result.rowcount
            print(f"      - user_sessions (normais): {result.rowcount}")

            # Remover user_establishments de usuários normais
            result = await conn.execute(
                text(
                    f"""
                DELETE FROM master.user_establishments
                WHERE user_id IN ({user_ids_str})
            """
                )
            )
            removed_counts["user_establishments"] = result.rowcount
            print(f"      - user_establishments (normais): {result.rowcount}")

            # Remover role_permissions concedidas por usuários normais
            result = await conn.execute(
                text(
                    f"""
                DELETE FROM master.role_permissions
                WHERE granted_by_user_id IN ({user_ids_str})
            """
                )
            )
            removed_counts["role_permissions"] = result.rowcount
            print(f"      - role_permissions (normais): {result.rowcount}")
        else:
            print(f"      - Nenhum usuário normal para limpar dependências")

        # PASSO 2: Remover dados de negócio
        print(f"\n   📋 Removendo dados de negócio...")

        # Remover establishments
        result = await conn.execute(text("DELETE FROM master.establishments"))
        removed_counts["establishments"] = result.rowcount
        print(f"      - establishments: {result.rowcount}")

        # Remover clients
        result = await conn.execute(text("DELETE FROM master.clients"))
        removed_counts["clients"] = result.rowcount
        print(f"      - clients: {result.rowcount}")

        # Remover contatos
        result = await conn.execute(text("DELETE FROM master.phones"))
        removed_counts["phones"] = result.rowcount
        print(f"      - phones: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.emails"))
        removed_counts["emails"] = result.rowcount
        print(f"      - emails: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.addresses"))
        removed_counts["addresses"] = result.rowcount
        print(f"      - addresses: {result.rowcount}")

        # PASSO 3: Remover usuários normais ANTES de remover companies
        if normal_users:
            print(f"\n   👥 Removendo usuários normais...")
            result = await conn.execute(
                text(
                    f"""
                DELETE FROM master.users
                WHERE id IN ({user_ids_str})
            """
                )
            )
            removed_counts["users_normal"] = result.rowcount
            print(f"      - usuários normais: {result.rowcount}")

        # PASSO 4: Remover people das empresas (preservando as de admin)
        print(f"\n   🧹 Removendo people de empresas (preservando admin)...")
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id IN (SELECT person_id FROM master.companies)
            AND id NOT IN (
                SELECT person_id FROM master.users WHERE person_id IS NOT NULL
            )
        """
            )
        )
        removed_counts["people_companies"] = result.rowcount
        print(f"      - people de empresas: {result.rowcount}")

        # PASSO 5: Agora remover companies (não tem mais people referenciando)
        result = await conn.execute(text("DELETE FROM master.companies"))
        removed_counts["companies"] = result.rowcount
        print(f"      - companies: {result.rowcount}")

        # PASSO 6: Limpar people órfãs restantes
        print(f"\n   🧹 Limpeza final de people órfãs...")
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE id NOT IN (
                SELECT person_id FROM master.users WHERE person_id IS NOT NULL
            )
        """
            )
        )
        removed_counts["people_final"] = result.rowcount
        print(f"      - people órfãs finais: {result.rowcount}")

        print(f"\n3️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Verificar preservação do sistema
        result = await conn.execute(
            text(
                """
            SELECT id, email_address FROM master.users
            ORDER BY id
        """
            )
        )
        remaining_users = result.fetchall()

        result = await conn.execute(text("SELECT COUNT(*) FROM master.menus"))
        final_menus = result.scalar()

        result = await conn.execute(text("SELECT COUNT(*) FROM master.roles"))
        final_roles = result.scalar()

        print(f"\n   ✅ SISTEMA PRESERVADO:")
        print(f"      - Usuários admin: {len(remaining_users)}")
        for user in remaining_users:
            print(f"        * ID {user.id}: {user.email_address}")
        print(f"      - Menus: {final_menus}")
        print(f"      - Roles: {final_roles}")

        # Verificar limpeza dos dados de negócio
        print(f"\n   🗑️ DADOS DE NEGÓCIO LIMPOS:")
        final_business = {}
        for table, desc in business_tables.items():
            result = await conn.execute(text(f"SELECT COUNT(*) FROM master.{table}"))
            count = result.scalar()
            final_business[table] = count
            status = "✅" if count == 0 else "⚠️"
            print(f"      {status} {desc}: {count}")

        result = await conn.execute(text("SELECT COUNT(*) FROM master.people"))
        final_people = result.scalar()
        print(f"      📋 People restantes: {final_people}")

        print(f"\n4️⃣ RESUMO FINAL:")
        total_removed = sum(removed_counts.values())
        print(f"   📊 Total removido: {total_removed} registros")

        print(f"\n   📋 DETALHES DA REMOÇÃO:")
        for key, count in removed_counts.items():
            if count > 0:
                print(f"      - {key}: {count}")

        # Status final
        business_clean = all(count == 0 for count in final_business.values())
        system_intact = len(remaining_users) > 0 and final_menus > 0 and final_roles > 0

        if business_clean and system_intact:
            print(f"\n   🎉 LIMPEZA SELETIVA CONCLUÍDA COM SUCESSO!")
            print(f"   ✅ Sistema preservado (admin, menus, roles)")
            print(f"   ✅ Dados de negócio limpos")
            print(f"   🚀 PRONTO PARA NOVOS CADASTROS COM ESTRUTURA MULTI-TENANT!")

            if len(remaining_users) == 1:
                admin_user = remaining_users[0]
                print(f"\n   🔑 LOGIN DO SISTEMA:")
                print(f"      Email: {admin_user.email_address}")
                print(f"      Senha: (a senha que você definiu)")
        else:
            print(f"\n   ⚠️  Limpeza com ressalvas:")
            if not system_intact:
                print(f"      🔧 Sistema comprometido - verificar admin/menus/roles")
            if not business_clean:
                remaining_business = sum(final_business.values())
                print(f"      🔧 Dados de negócio restantes: {remaining_business}")


async def main():
    """Função principal"""
    try:
        await cleanup_business_data_preserve_system()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
