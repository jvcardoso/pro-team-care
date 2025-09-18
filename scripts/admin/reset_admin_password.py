#!/usr/bin/env python3
"""
Script para resetar senha do usuário admin
🔐 Use apenas para desenvolvimento/teste
"""

import asyncio

import asyncpg
from passlib.context import CryptContext

# Configurações do banco
DB_HOST = "192.168.11.62"
DB_PORT = 5432
DB_USERNAME = "postgres"
DB_PASSWORD = "Jvc@1702"
DB_DATABASE = "pro_team_care_11"
DB_SCHEMA = "master"

# Hash de senha (usar método simples para evitar erro do bcrypt)
import hashlib


def simple_hash(password: str) -> str:
    """Hash simples para teste"""
    return hashlib.sha256(password.encode()).hexdigest()


async def reset_password():
    """Resetar senha do admin"""

    email = "admin@proteamcare.com"
    new_password = "admin123"

    # Hash da nova senha
    hashed_password = simple_hash(new_password)

    # Conectar ao banco
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        server_settings={"search_path": f"{DB_SCHEMA}, public"},
    )

    try:
        # Atualizar senha
        result = await connection.execute(
            """
            UPDATE users
            SET password = $1
            WHERE email_address = $2
        """,
            hashed_password,
            email,
        )

        print(f"✅ Senha resetada com sucesso!")
        print(f"📧 Email: {email}")
        print(f"🔑 Nova senha: {new_password}")
        print(f"🔐 Hash: {hashed_password}")

    except Exception as e:
        print(f"❌ Erro ao resetar senha: {e}")

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(reset_password())
