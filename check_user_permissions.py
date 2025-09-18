#!/usr/bin/env python3
"""
Script para verificar permissões do usuário de teste
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def check_user_permissions():
    print("=== VERIFICANDO PERMISSÕES DO USUÁRIO ===")

    user_email = "teste_02@teste.com"

    try:
        async for db in get_db():
            # Buscar usuário
            user_query = text(
                """
                SELECT u.id, u.email_address, u.company_id, u.establishment_id, u.context_type, u.is_system_admin
                FROM master.users u
                WHERE u.email_address = :email
            """
            )
            user_result = await db.execute(user_query, {"email": user_email})
            user = user_result.fetchone()

            if not user:
                print(f"❌ Usuário {user_email} não encontrado")
                return

            print(f"👤 Usuário: {user.email_address} (ID: {user.id})")
            print(f"🏢 Empresa: {user.company_id}")
            print(f"🏥 Estabelecimento: {user.establishment_id}")
            print(f"🔍 Contexto: {user.context_type}")
            print(f"👑 System Admin: {user.is_system_admin}")
            print()

            # Buscar roles do usuário
            roles_query = text(
                """
                SELECT r.id, r.name, ur.context_id, ur.status
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id AND ur.status = 'active' AND ur.deleted_at IS NULL
            """
            )
            roles_result = await db.execute(roles_query, {"user_id": user.id})
            roles = roles_result.fetchall()

            print(f"🎭 Roles do usuário ({len(roles)}):")
            for role in roles:
                print(
                    f"   - {role.name} (ID: {role.id}, Context: {role.context_id}, Status: {role.status})"
                )
            print()

            # Buscar permissões do usuário
            permissions_query = text(
                """
                SELECT DISTINCT p.name, p.context_level, rp.role_id, r.name as role_name
                FROM master.user_roles ur
                JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                JOIN master.permissions p ON rp.permission_id = p.id
                JOIN master.roles r ON ur.role_id = r.id
                WHERE ur.user_id = :user_id
                  AND ur.status = 'active'
                  AND ur.deleted_at IS NULL
                  AND p.is_active = true
                ORDER BY p.name
            """
            )
            permissions_result = await db.execute(
                permissions_query, {"user_id": user.id}
            )
            permissions = permissions_result.fetchall()

            print(f"🔐 Permissões do usuário ({len(permissions)}):")
            for perm in permissions:
                print(
                    f"   - {perm.name} (Context: {perm.context_level}, Role: {perm.role_name})"
                )
            print()

            # Verificar permissões específicas que testamos
            specific_permissions = [
                "companies.view",
                "establishments.view",
                "users.view",
            ]
            print("🔍 Verificação de permissões específicas:")
            for perm_name in specific_permissions:
                has_perm_query = text(
                    """
                    SELECT COUNT(*) > 0 as has_permission
                    FROM master.user_roles ur
                    JOIN master.role_permissions rp ON ur.role_id = rp.role_id
                    JOIN master.permissions p ON rp.permission_id = p.id
                    WHERE ur.user_id = :user_id
                      AND p.name = :perm_name
                      AND ur.status = 'active'
                      AND ur.deleted_at IS NULL
                      AND p.is_active = true
                """
                )
                has_perm_result = await db.execute(
                    has_perm_query, {"user_id": user.id, "perm_name": perm_name}
                )
                has_perm = has_perm_result.scalar()
                status = "✅ TEM" if has_perm else "❌ NÃO TEM"
                print(f"   - {perm_name}: {status}")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_user_permissions())
