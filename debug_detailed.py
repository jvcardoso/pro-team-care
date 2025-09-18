#!/usr/bin/env python3
"""
Debug detalhado do sistema de permissões
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.cache.permission_cache import permission_cache
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User
from app.presentation.decorators.hybrid_permissions import hybrid_checker


async def debug_detailed():
    print("=== DEBUG DETALHADO SISTEMA DE PERMISSÕES ===")

    try:
        await permission_cache.init_redis()

        user_id = 5
        permission = "users_view"
        context_type = "system"
        context_id = 1

        print(
            f"\n1. Testando usuário {user_id} com permissão '{permission}' no contexto '{context_type}' (ID: {context_id})"
        )

        # Teste direto do cache
        print("\n   1.1. Teste direto do cache de permissões:")
        has_perm_cache = await permission_cache.has_permission(
            user_id, permission, context_type, context_id
        )
        print(f"      ✅ permission_cache.has_permission(): {has_perm_cache}")

        # Teste sem context_id (NULL)
        print("\n   1.2. Teste sem context_id (NULL):")
        has_perm_null = await permission_cache.has_permission(
            user_id, permission, context_type, None
        )
        print(
            f"      ✅ permission_cache.has_permission(context_id=None): {has_perm_null}"
        )

        # Teste do híbrido
        print("\n   1.3. Teste do decorator híbrido:")
        has_hybrid = await hybrid_checker.check_access(
            user_id, permission, None, context_type, context_id
        )
        print(f"      ✅ hybrid_checker.check_access(): {has_hybrid}")

        # Verificar dados no banco diretamente
        print("\n2. Verificando dados do usuário no banco:")
        async for db in get_db():
            # Roles do usuário
            result = await db.execute(
                text(
                    """
                SELECT ur.context_type, ur.context_id, r.name as role_name, r.level
                FROM master.user_roles ur
                JOIN master.roles r ON r.id = ur.role_id
                WHERE ur.user_id = :user_id AND ur.status = 'active'
            """
                ),
                {"user_id": user_id},
            )

            roles = result.fetchall()
            for role in roles:
                print(
                    f"   👤 Role: {role.role_name} (nível {role.level}) - Contexto: {role.context_type} (ID: {role.context_id})"
                )

            # Permissões específicas
            result = await db.execute(
                text(
                    """
                SELECT DISTINCT p.name, p.description, ur.context_type, ur.context_id
                FROM master.user_roles ur
                JOIN master.role_permissions rp ON rp.role_id = ur.role_id
                JOIN master.permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = :user_id
                  AND ur.status = 'active'
                  AND p.name = :permission
            """
                ),
                {"user_id": user_id, "permission": permission},
            )

            permissions = result.fetchall()
            if permissions:
                print(f"\n   🔐 Permissão '{permission}' encontrada:")
                for perm in permissions:
                    print(
                        f"      - Contexto: {perm.context_type} (ID: {perm.context_id})"
                    )
                    print(f"      - Descrição: {perm.description}")
            else:
                print(f"   ❌ Permissão '{permission}' NÃO encontrada para o usuário")

            # Listar TODAS as permissões do usuário
            result = await db.execute(
                text(
                    """
                SELECT DISTINCT p.name, ur.context_type, ur.context_id
                FROM master.user_roles ur
                JOIN master.role_permissions rp ON rp.role_id = ur.role_id
                JOIN master.permissions p ON p.id = rp.permission_id
                WHERE ur.user_id = :user_id
                  AND ur.status = 'active'
                ORDER BY ur.context_type, p.name
                LIMIT 50
            """
                ),
                {"user_id": user_id},
            )

            all_perms = result.fetchall()
            print(f"\n   📋 Todas as permissões do usuário (primeiras 50):")
            for perm in all_perms:
                print(f"      ✓ {perm.name} - {perm.context_type}:{perm.context_id}")

            break

        print(f"\n3. Teste final: Simulate endpoint call")
        print(
            f"   Endpoint esperando: permission='{permission}', context='{context_type}'"
        )
        print(f"   Cache retorna: {has_perm_null} (sem context_id)")
        print(f"   Cache retorna: {has_perm_cache} (com context_id={context_id})")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_detailed())
