#!/usr/bin/env python3
"""
Script para criar entrada no menu para o Database Admin
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from datetime import datetime

# Configuração do banco
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/pro_team_care_11"

async def create_db_admin_menu():
    """Cria entrada no menu para o Database Admin"""

    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Verificar se já existe
            result = await session.execute(
                text("SELECT id FROM master.menus WHERE slug = 'db-admin' AND parent_id IS NULL")
            )
            existing = result.fetchone()

            if existing:
                print("✅ Menu Database Admin já existe!")
                return

            # Encontrar um bom sort_order (último + 10)
            result = await session.execute(
                text("SELECT COALESCE(MAX(sort_order), 0) + 10 as next_sort FROM master.menus WHERE parent_id IS NULL")
            )
            next_sort = result.fetchone()[0]

            # Inserir novo menu
            insert_query = text("""
                INSERT INTO master.menus (
                    name, slug, url, route_name, level, sort_order,
                    menu_type, status, is_visible, visible_in_menu,
                    permission_name, company_specific, establishment_specific,
                    icon, description, created_at, updated_at
                ) VALUES (
                    '🗄️ Database Admin', 'db-admin', '/simple_db_admin.html', NULL, 0, :sort_order,
                    'external_link', 'active', true, true,
                    'admin.system.database.view', false, false,
                    'database', 'Interface de administração simplificada do banco de dados',
                    NOW(), NOW()
                )
            """)

            await session.execute(insert_query, {"sort_order": next_sort})
            await session.commit()

            print("✅ Menu Database Admin criado com sucesso!")
            print(f"   - Nome: 🗄️ Database Admin")
            print(f"   - Slug: db-admin")
            print(f"   - URL: /simple_db_admin.html")
            print(f"   - Permissão: admin.system.database.view")
            print(f"   - Sort Order: {next_sort}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Erro ao criar menu: {e}")
            raise
        finally:
            await session.close()

async def main():
    print("🚀 Criando entrada no menu para Database Admin...")
    await create_db_admin_menu()
    print("✅ Processo concluído!")

if __name__ == "__main__":
    asyncio.run(main())