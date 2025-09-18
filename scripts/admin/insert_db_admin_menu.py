#!/usr/bin/env python3
"""
Script simples para inserir entrada do Database Admin no menu
Usa a mesma configuração do backend
"""
import asyncio
import os
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


async def insert_menu_entry():
    """Insere entrada do Database Admin no menu"""

    # Usar mesma configuração do settings.py
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_username = os.getenv("DB_USERNAME", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_database = os.getenv("DB_DATABASE", "pro_team_care_11")

    # URL encode da senha
    encoded_password = quote_plus(db_password)

    database_url = f"postgresql+asyncpg://{db_username}:{encoded_password}@{db_host}:{db_port}/{db_database}"

    print(f"🔌 Conectando ao banco: {db_host}:{db_port}/{db_database}")

    engine = create_async_engine(database_url, echo=False)

    async with AsyncSession(engine) as session:
        try:
            # Verificar se já existe
            result = await session.execute(
                text(
                    "SELECT id FROM master.menus WHERE slug = 'db-admin' AND parent_id IS NULL"
                )
            )
            existing = result.fetchone()

            if existing:
                print("✅ Menu Database Admin já existe!")
                return

            # Encontrar sort_order
            result = await session.execute(
                text(
                    "SELECT COALESCE(MAX(sort_order), 0) + 10 as next_sort FROM master.menus WHERE parent_id IS NULL"
                )
            )
            next_sort = result.fetchone()[0]

            # Inserir menu sem especificar ID (deixe o banco gerar)
            insert_sql = """
                INSERT INTO master.menus (
                    parent_id, name, slug, url, level, sort_order, type, is_active,
                    is_visible, visible_in_menu, permission_name, icon, description,
                    created_at, updated_at
                ) VALUES (
                    NULL, '🗄️ Database Admin', 'db-admin', '/simple_db_admin.html', 0, :sort_order,
                    'menu', true, true, true, 'admin.system.database.view', 'database',
                    'Interface de administração simplificada do banco de dados',
                    NOW(), NOW()
                )
            """

            await session.execute(text(insert_sql), {"sort_order": next_sort})
            await session.commit()

            print("✅ Menu Database Admin criado com sucesso!")
            print(f"   📍 URL: /simple_db_admin.html")
            print(f"   🔐 Permissão: admin.system.database.view")
            print(f"   📊 Sort Order: {next_sort}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Erro: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    print("🚀 Inserindo entrada do Database Admin no menu...")
    asyncio.run(insert_menu_entry())
    print("✅ Concluído!")
