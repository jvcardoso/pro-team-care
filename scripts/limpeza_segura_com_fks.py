#!/usr/bin/env python3
"""
LIMPEZA SEGURA COM FOREIGN KEYS
Limpeza respeitando dependências de foreign keys
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def safe_cleanup():
    """Limpeza segura respeitando foreign keys"""

    print("🧹 LIMPEZA SEGURA COM FOREIGN KEYS")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ ANÁLISE DE DEPENDÊNCIAS:")

        # Verificar que usuários têm referências
        result = await conn.execute(
            text(
                """
            SELECT u.id, u.email_address,
                   COUNT(rp.id) as role_permissions_count
            FROM master.users u
            LEFT JOIN master.role_permissions rp ON rp.granted_by = u.id
            WHERE u.email_address LIKE '%teste%'
               OR u.email_address LIKE '%test%'
            GROUP BY u.id, u.email_address
        """
            )
        )

        problem_users = list(result)
        for user in problem_users:
            print(
                f"   👤 User {user.id} ({user.email_address}): {user.role_permissions_count} referências"
            )

        print("\n2️⃣ EXECUTANDO LIMPEZA SEGURA:")

        # 1. Limpar role_permissions primeiro
        result = await conn.execute(
            text(
                """
            DELETE FROM master.role_permissions
            WHERE granted_by IN (
                SELECT id FROM master.users
                WHERE email_address LIKE '%teste%'
                   OR email_address LIKE '%test%'
                   OR email_address LIKE '%@multitenant.com'
                   OR email_address LIKE '%@rls.com'
            )
        """
            )
        )
        print(f"   🗑️ Role permissions removidas: {result.rowcount}")

        # 2. Limpar user_roles
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_roles
            WHERE user_id IN (
                SELECT id FROM master.users
                WHERE email_address LIKE '%teste%'
                   OR email_address LIKE '%test%'
                   OR email_address LIKE '%@multitenant.com'
                   OR email_address LIKE '%@rls.com'
            )
        """
            )
        )
        print(f"   🗑️ User roles removidas: {result.rowcount}")

        # 3. Limpar user_sessions
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_sessions
            WHERE user_id IN (
                SELECT id FROM master.users
                WHERE email_address LIKE '%teste%'
                   OR email_address LIKE '%test%'
                   OR email_address LIKE '%@multitenant.com'
                   OR email_address LIKE '%@rls.com'
            )
        """
            )
        )
        print(f"   🗑️ User sessions removidas: {result.rowcount}")

        # 4. Limpar user_establishments
        result = await conn.execute(
            text(
                """
            DELETE FROM master.user_establishments
            WHERE user_id IN (
                SELECT id FROM master.users
                WHERE email_address LIKE '%teste%'
                   OR email_address LIKE '%test%'
                   OR email_address LIKE '%@multitenant.com'
                   OR email_address LIKE '%@rls.com'
            )
        """
            )
        )
        print(f"   🗑️ User establishments removidas: {result.rowcount}")

        # 5. Agora remover addresses, emails, phones (sem FK dependencies)
        result = await conn.execute(text("DELETE FROM master.addresses"))
        print(f"   🗑️ Addresses removidos: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.emails"))
        print(f"   🗑️ Emails removidos: {result.rowcount}")

        result = await conn.execute(text("DELETE FROM master.phones"))
        print(f"   🗑️ Phones removidos: {result.rowcount}")

        # 6. Remover clients de teste
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
        print(f"   🗑️ Clients de teste removidos: {result.rowcount}")

        # 7. Remover establishments de teste
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
        print(f"   🗑️ Establishments de teste removidos: {result.rowcount}")

        # 8. AGORA remover usuários de teste (dependências já limpas)
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
        print(f"   🗑️ Users de teste removidos: {result.rowcount}")

        # 9. Remover people de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE name LIKE '%Teste%'
            OR name LIKE '%Test%'
            OR name LIKE '%TESTE%'
            OR tax_id LIKE '99%'
            OR (name LIKE '%João Silva%' AND tax_id LIKE '%12345%')
        """
            )
        )
        print(f"   🗑️ People de teste removidos: {result.rowcount}")

        # 10. Remover companies órfãs
        result = await conn.execute(
            text(
                """
            DELETE FROM master.companies
            WHERE person_id NOT IN (SELECT id FROM master.people)
        """
            )
        )
        print(f"   🗑️ Companies órfãs removidas: {result.rowcount}")

        print("\n3️⃣ VERIFICAÇÃO FINAL:")

        # Contagem final das tabelas principais
        tables = ["people", "users", "companies", "menus", "establishments", "clients"]
        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM master.{table}"))
            count = result.scalar()
            print(f"   📊 {table:15}: {count:6} registros")

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

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users u
            LEFT JOIN master.people p ON p.id = u.person_id
            WHERE p.id IS NULL
        """
            )
        )
        orphan_users = result.scalar()

        print(f"\n4️⃣ INTEGRIDADE:")
        print(f"   📋 Pessoas órfãs: {orphan_people}")
        print(f"   📋 Users órfãos: {orphan_users}")

        # Verificar constraints multi-tenant
        result = await conn.execute(
            text(
                """
            SELECT conname FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname IN ('people', 'users')
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%company_id%'
        """
            )
        )
        mt_constraints = [row.conname for row in result]

        print(f"   📋 Constraints multi-tenant ativas: {len(mt_constraints)}")
        for constraint in mt_constraints:
            print(f"      - {constraint}")

        # Status final
        success = (
            orphan_people == 0
            and orphan_users == 0
            and len(mt_constraints) >= 2  # people + users
        )

        if success:
            print(f"\n   🎉 LIMPEZA SEGURA CONCLUÍDA!")
            print(f"   ✅ Base de dados otimizada")
            print(f"   ✅ Integridade multi-tenant preservada")
            print(f"   ✅ Foreign keys respeitadas")
            print(f"\n   🚀 SISTEMA LIMPO E FUNCIONAL!")
        else:
            print(f"\n   ⚠️  Verificar integridade dos dados")


async def main():
    """Função principal"""
    try:
        await safe_cleanup()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
