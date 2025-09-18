#!/usr/bin/env python3
"""
Debug script para testar permissões granulares
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.cache.permission_cache import permission_cache
from app.infrastructure.database import get_db


async def debug_permissions():
    print("=== DEBUG SISTEMA DE PERMISSÕES ===")

    try:
        # Verificar se o cache de permissões está funcionando
        print("1. Testando cache de permissões...")

        # Verificar permissão diretamente
        has_permission = await permission_cache.has_permission(
            user_id=5, permission="users_view", context_type="system", context_id=1
        )

        print(f"   ✅ has_permission(5, 'users_view', 'system', 1): {has_permission}")

        # Verificar com establishment
        has_permission_est = await permission_cache.has_permission(
            user_id=5,
            permission="users_view",
            context_type="establishment",
            context_id=None,
        )

        print(
            f"   ✅ has_permission(5, 'users_view', 'establishment', None): {has_permission_est}"
        )

        # Verificar dados no banco diretamente
        print("\n2. Verificando dados no banco...")

        async for db in get_db():
            # Verificar role do usuário
            result = await db.execute(
                text(
                    """
                SELECT ur.context_type, ur.context_id, r.name as role_name
                FROM master.user_roles ur
                JOIN master.roles r ON r.id = ur.role_id
                WHERE ur.user_id = 5
            """
                )
            )

            user_role = result.fetchone()
            if user_role:
                print(f"   👤 Role: {user_role.role_name}")
                print(
                    f"   🔗 Contexto: {user_role.context_type} (ID: {user_role.context_id})"
                )

            # Verificar se permissão existe na role
            result = await db.execute(
                text(
                    """
                SELECT COUNT(*) as count
                FROM master.user_roles ur
                JOIN master.role_permissions rp ON rp.role_id = ur.role_id
                JOIN master.permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = 5 AND p.name = 'users_view'
            """
                )
            )

            perm_count = result.scalar()
            print(f"   🔐 Permissão 'users_view' na role: {perm_count} vezes")

            # Listar todas as permissões do usuário
            result = await db.execute(
                text(
                    """
                SELECT p.name, p.description
                FROM master.user_roles ur
                JOIN master.role_permissions rp ON rp.role_id = ur.role_id
                JOIN master.permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = 5
                ORDER BY p.name
                LIMIT 10
            """
                )
            )

            print(f"\n3. Primeiras 10 permissões do usuário:")
            for perm in result.fetchall():
                print(f"   ✓ {perm.name}")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_permissions())
