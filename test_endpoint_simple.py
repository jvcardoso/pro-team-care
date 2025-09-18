#!/usr/bin/env python3
"""
Teste simples para verificar o endpoint de usuários
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import select

from app.infrastructure.cache.permission_cache import permission_cache
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User
from app.presentation.decorators.hybrid_permissions import hybrid_checker


async def test_endpoint_logic():
    print("=== TESTE SIMPLES ENDPOINT ===")

    try:
        # Inicializar cache
        await permission_cache.init_redis()

        user_id = 5
        permission = "users_view"
        context_type = "system"

        print(f"1. Testando lógica similar ao endpoint users/")
        print(f"   Usuário: {user_id}")
        print(f"   Permissão: {permission}")
        print(f"   Contexto: {context_type}")

        # Simular o que o decorator faz
        print(f"\n2. Simulando decorator com context_id = None:")
        context_id = None

        # Aplicar nossa nova lógica
        if context_type == "system" and context_id is None:
            context_id = 1
            print(f"   ✅ context_id foi alterado de None para {context_id}")

        # Testar permissão
        has_access = await hybrid_checker.check_access(
            user_id, permission, None, context_type, context_id
        )

        print(f"   ✅ Resultado: {has_access}")

        # Testar consulta direta ao banco (simular o que o endpoint faz)
        print(f"\n3. Testando consulta ao banco:")
        async for db in get_db():
            # Simular query básica do endpoint users
            result = await db.execute(select(User.id, User.email).limit(1))
            user = result.first()
            if user:
                print(f"   ✅ Consulta ao banco funcionou: {user.email}")
            else:
                print(f"   ❌ Nenhum usuário encontrado")
            break

        print(f"\n✅ Teste concluído com sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_endpoint_logic())
