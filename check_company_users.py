#!/usr/bin/env python3
"""
Script para verificar usuários de empresa com permissões
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def check_company_users():
    print("=== VERIFICANDO USUÁRIOS DE EMPRESA COM PERMISSÕES ===")

    try:
        async for db in get_db():
            # Usuários que NÃO são system admin mas têm permissões
            company_users_query = text(
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
                  AND u.is_system_admin = false
                  AND u.company_id IS NOT NULL
                GROUP BY u.id, u.email_address, u.company_id, u.establishment_id, u.context_type, u.is_system_admin, r.name
                ORDER BY u.email_address
            """
            )
            company_users_result = await db.execute(company_users_query)
            company_users = company_users_result.fetchall()

            print(f"🏢 Usuários de empresa com permissões ({len(company_users)}):")
            for cu in company_users:
                print(f"   - {cu.email_address} (ID: {cu.user_id})")
                print(f"     Empresa: {cu.company_id}, Contexto: {cu.context_type}")
                print(f"     System Admin: {cu.is_system_admin}")
                print(f"     Role: {cu.role_name} ({cu.perm_count} permissões)")
                print()

                # Verificar permissões específicas
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
                    specific_perms_query, {"user_id": cu.user_id}
                )
                specific_perms = specific_result.fetchall()

                if specific_perms:
                    print(f"     🔍 Permissões específicas:")
                    for sp in specific_perms:
                        print(f"        - {sp.name} (Context: {sp.context_level})")
                    print()

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_company_users())
