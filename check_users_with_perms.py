#!/usr/bin/env python3
"""
Script para verificar usuários que têm permissões funcionais
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def check_users_with_perms():
    print("=== VERIFICANDO USUÁRIOS COM PERMISSÕES FUNCIONAIS ===")

    try:
        async for db in get_db():
            # Usuários com roles que têm permissões
            users_with_perms_query = text(
                """
                SELECT DISTINCT
                    u.email_address,
                    u.id as user_id,
                    u.company_id,
                    u.establishment_id,
                    u.context_type,
                    u.is_system_admin,
                    r.name as role_name,
                    COUNT(rp.permission_id) as perm_count
                FROM master.users u
                JOIN master.user_roles ur ON u.id = ur.user_id
                JOIN master.roles r ON ur.role_id = r.id
                JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE u.is_active = true
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND r.is_active = true
                GROUP BY u.id, u.email_address, u.company_id, u.establishment_id, u.context_type, u.is_system_admin, r.name
                ORDER BY u.email_address
            """
            )
            users_perms_result = await db.execute(users_with_perms_query)
            users_perms = users_perms_result.fetchall()

            print(f"✅ Usuários com permissões funcionais ({len(users_perms)}):")
            for up in users_perms:
                print(f"   - {up.email_address} (ID: {up.user_id})")
                print(f"     Role: {up.role_name}")
                print(f"     Empresa: {up.company_id}, Contexto: {up.context_type}")
                print(f"     System Admin: {up.is_system_admin}")
                print(f"     Permissões: {up.perm_count}")
                print()

            # Verificar permissões específicas dos usuários
            for user in users_perms:
                specific_perms_query = text(
                    """
                    SELECT DISTINCT p.name, p.context_level
                    FROM master.user_roles ur
                    JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                    JOIN master.permissions p ON rp.permission_id = p.id
                    WHERE ur.user_id = :user_id
                      AND ur.status = 'active'
                      AND ur.deleted_at IS NULL
                      AND p.is_active = true
                      AND p.name IN ('companies.view', 'establishments.view', 'users.view')
                    ORDER BY p.name
                """
                )
                specific_result = await db.execute(
                    specific_perms_query, {"user_id": user.user_id}
                )
                specific_perms = specific_result.fetchall()

                if specific_perms:
                    print(f"   🔍 Permissões específicas de {user.email_address}:")
                    for sp in specific_perms:
                        print(f"     - {sp.name} (Context: {sp.context_level})")
                    print()

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_users_with_perms())
