#!/usr/bin/env python3
"""
Script para verificar todas as permissões e roles do sistema
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def check_system_permissions():
    print("=== VERIFICANDO PERMISSÕES DO SISTEMA ===")

    try:
        async for db in get_db():
            # Verificar todas as permissões disponíveis
            permissions_query = text(
                """
                SELECT id, name, context_level, module, action, resource, is_active
                FROM master.permissions
                WHERE is_active = true
                ORDER BY name
            """
            )
            permissions_result = await db.execute(permissions_query)
            permissions = permissions_result.fetchall()

            print(f"🔐 Permissões disponíveis no sistema ({len(permissions)}):")
            for perm in permissions:
                print(
                    f"   - {perm.name} (Context: {perm.context_level}, Module: {perm.module})"
                )
            print()

            # Verificar todos os roles
            roles_query = text(
                """
                SELECT id, name, description, is_active
                FROM master.roles
                WHERE is_active = true
                ORDER BY name
            """
            )
            roles_result = await db.execute(roles_query)
            roles = roles_result.fetchall()

            print(f"🎭 Roles disponíveis no sistema ({len(roles)}):")
            for role in roles:
                print(f"   - {role.name} (ID: {role.id})")
            print()

            # Verificar quais roles têm permissões
            roles_with_perms_query = text(
                """
                SELECT DISTINCT r.name as role_name, r.id as role_id, COUNT(rp.permission_id) as perm_count
                FROM master.roles r
                LEFT JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE r.is_active = true
                GROUP BY r.id, r.name
                ORDER BY r.name
            """
            )
            roles_perms_result = await db.execute(roles_with_perms_query)
            roles_perms = roles_perms_result.fetchall()

            print("📊 Roles com permissões:")
            for rp in roles_perms:
                status = "✅ TEM" if rp.perm_count > 0 else "❌ SEM"
                print(
                    f"   - {rp.role_name} (ID: {rp.role_id}): {status} ({rp.perm_count} permissões)"
                )
            print()

            # Verificar usuários com roles
            users_with_roles_query = text(
                """
                SELECT DISTINCT u.email_address, u.id as user_id, COUNT(ur.role_id) as role_count
                FROM master.users u
                JOIN master.user_roles ur ON u.id = ur.user_id
                WHERE u.is_active = true AND ur.status = 'active' AND ur.deleted_at IS NULL
                GROUP BY u.id, u.email_address
                ORDER BY u.email_address
            """
            )
            users_roles_result = await db.execute(users_with_roles_query)
            users_roles = users_roles_result.fetchall()

            print(f"👥 Usuários com roles ({len(users_roles)}):")
            for ur in users_roles:
                print(
                    f"   - {ur.email_address} (ID: {ur.user_id}): {ur.role_count} roles"
                )
            print()

            # Verificar usuários sem permissões
            users_without_perms_query = text(
                """
                SELECT DISTINCT u.email_address, u.id as user_id
                FROM master.users u
                JOIN master.user_roles ur ON u.id = ur.user_id
                LEFT JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                WHERE u.is_active = true
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND rp.permission_id IS NULL
                ORDER BY u.email_address
            """
            )
            users_no_perms_result = await db.execute(users_without_perms_query)
            users_no_perms = users_no_perms_result.fetchall()

            print(f"⚠️ Usuários com roles mas SEM permissões ({len(users_no_perms)}):")
            for unp in users_no_perms:
                print(f"   - {unp.email_address} (ID: {unp.user_id})")
            print()

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_system_permissions())
