#!/usr/bin/env python3
"""
Script para criar usuário administrador de teste
🔐 Use apenas para desenvolvimento/teste inicial
"""

import asyncio
from datetime import datetime

import asyncpg
from passlib.context import CryptContext

# Configurações do banco (mesmas do .env)
DB_HOST = "192.168.11.62"
DB_PORT = 5432
DB_USERNAME = "postgres"
DB_PASSWORD = "Jvc@1702"
DB_DATABASE = "pro_team_care_11"
DB_SCHEMA = "master"

# Hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user():
    """Criar usuário admin de teste"""

    # Dados do usuário admin
    email = "admin@proteamcare.com"
    password = "ProTeam123!"  # Senha forte para produção

    # Hash da senha
    hashed_password = pwd_context.hash(password)

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
        # Verificar se usuário já existe
        existing_user = await connection.fetchrow(
            "SELECT email_address FROM users WHERE email_address = $1", email
        )

        if existing_user:
            print(f"✅ Usuário {email} já existe!")
            return

        # Primeiro, criar uma pessoa (person_id é obrigatório)
        person_id = await connection.fetchval(
            """
            INSERT INTO people (
                first_name,
                last_name,
                full_name,
                document_number,
                created_at,
                updated_at
            ) VALUES (
                'Admin',
                'Sistema',
                'Admin Sistema',
                '00000000000',
                $1,
                $1
            ) RETURNING id
        """,
            datetime.utcnow(),
        )

        # Criar usuário admin
        user_id = await connection.fetchval(
            """
            INSERT INTO users (
                person_id,
                email_address,
                password,
                is_active,
                is_system_admin,
                created_at,
                updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $6
            ) RETURNING id
        """,
            person_id,
            email,
            hashed_password,
            True,
            True,
            datetime.utcnow(),
        )

        print(f"✅ Usuário admin criado com sucesso!")
        print(f"📧 Email: {email}")
        print(f"🔑 Senha: {password}")
        print(f"👤 User ID: {user_id}")
        print(f"🆔 Person ID: {person_id}")

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(create_admin_user())
