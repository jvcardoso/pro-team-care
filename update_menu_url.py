#!/usr/bin/env python3
"""
Script para atualizar URL do menu de usuários de /admin/users para /admin/usuarios
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"

async def update_menu_url():
    """Atualiza a URL do menu de usuários no banco de dados"""

    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        try:
            # Primeiro, verificar o menu atual
            print("🔍 Verificando menu atual...")
            result = await conn.execute(text("""
                SELECT id, name, url
                FROM master.menus
                WHERE url = '/admin/users'
                AND deleted_at IS NULL
            """))

            current_menu = result.fetchone()
            if current_menu:
                print(f"📝 Menu encontrado: ID={current_menu[0]}, Nome='{current_menu[1]}', URL='{current_menu[2]}'")

                # Atualizar a URL
                print("🔄 Atualizando URL para '/admin/usuarios'...")
                await conn.execute(text("""
                    UPDATE master.menus
                    SET url = '/admin/usuarios'
                    WHERE url = '/admin/users'
                    AND deleted_at IS NULL
                """))

                print("✅ URL do menu atualizada com sucesso!")
            else:
                print("⚠️  Menu com URL '/admin/users' não encontrado")

        except Exception as e:
            print(f"❌ Erro ao atualizar menu: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(update_menu_url())