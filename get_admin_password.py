#!/usr/bin/env python3
"""
Script para obter senha de usuário admin
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def get_admin_password():
    print("=== OBTENDO SENHA DE USUÁRIO ADMIN ===")

    try:
        async for db in get_db():
            # Buscar senha do admin@teste.com
            password_query = text(
                """
                SELECT u.email_address, u.password, u.is_system_admin
                FROM master.users u
                WHERE u.email_address = :email
            """
            )
            password_result = await db.execute(
                password_query, {"email": "admin@teste.com"}
            )
            user = password_result.fetchone()

            if user:
                print(f"👤 Usuário: {user.email_address}")
                print(f"🔑 Senha (hash): {user.password}")
                print(f"👑 System Admin: {user.is_system_admin}")
                print()
                print("💡 Para testar login, use a senha real (não o hash)")
                print("   Senhas comuns de teste: 'admin123', 'password', 'teste123'")
            else:
                print("❌ Usuário não encontrado")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_admin_password())
