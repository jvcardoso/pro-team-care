#!/usr/bin/env python3
"""
Script para inserir menu de Estabelecimentos no sistema
Baseado no padrão dos scripts existentes de menu
"""
import asyncio
import os
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


async def insert_establishments_menu():
    """Insere menu de Estabelecimentos no sistema"""

    # Usar mesma configuração do settings.py
    db_host = os.getenv("DB_HOST", "192.168.11.62")
    db_port = os.getenv("DB_PORT", "5432")
    db_username = os.getenv("DB_USERNAME", "postgres")
    db_password = os.getenv("DB_PASSWORD", "Jvc@1702")
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
                    "SELECT id FROM master.menus WHERE slug = 'estabelecimentos' AND parent_id IS NOT NULL"
                )
            )
            existing = result.fetchone()

            if existing:
                print("✅ Menu Estabelecimentos já existe!")
                return

            # Buscar menu pai "Administração"
            result = await session.execute(
                text(
                    "SELECT id FROM master.menus WHERE slug = 'administracao' AND parent_id IS NULL"
                )
            )
            parent_menu = result.fetchone()

            if not parent_menu:
                print("❌ Menu pai 'Administração' não encontrado!")
                # Criar como menu raiz
                parent_id = None
                level = 0
            else:
                parent_id = parent_menu[0]
                level = 1
                print(f"✅ Menu pai encontrado: ID {parent_id}")

            # Encontrar sort_order
            if parent_id:
                result = await session.execute(
                    text(
                        "SELECT COALESCE(MAX(sort_order), 0) + 1 as next_sort FROM master.menus WHERE parent_id = :parent_id"
                    ),
                    {"parent_id": parent_id},
                )
            else:
                result = await session.execute(
                    text(
                        "SELECT COALESCE(MAX(sort_order), 0) + 10 as next_sort FROM master.menus WHERE parent_id IS NULL"
                    )
                )
            next_sort = result.fetchone()[0]

            # Obter próximo ID disponível
            result = await session.execute(
                text("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM master.menus")
            )
            next_id = result.fetchone()[0]

            # Inserir menu com ID específico
            insert_sql = """
                INSERT INTO master.menus (
                    id, parent_id, name, slug, url, level, sort_order, type, is_active,
                    is_visible, visible_in_menu, permission_name, icon, description,
                    created_at, updated_at
                ) VALUES (
                    :id, :parent_id, 'Estabelecimentos', 'estabelecimentos', '/admin/estabelecimentos', :level, :sort_order,
                    'menu', true, true, true, 'establishments.view', 'Building2',
                    'Gerenciar estabelecimentos do sistema',
                    NOW(), NOW()
                )
            """

            await session.execute(
                text(insert_sql),
                {
                    "id": next_id,
                    "parent_id": parent_id,
                    "level": level,
                    "sort_order": next_sort,
                },
            )
            await session.commit()

            print("✅ Menu Estabelecimentos criado com sucesso!")
            print(f"   📍 URL: /admin/estabelecimentos")
            print(f"   🔐 Permissão: establishments.view")
            print(f"   📊 Sort Order: {next_sort}")
            if parent_id:
                print(f"   👆 Pai: Administração (ID: {parent_id})")

        except Exception as e:
            await session.rollback()
            print(f"❌ Erro: {e}")
            raise
        finally:
            await session.close()

    print("✅ Script concluído!")


if __name__ == "__main__":
    # Carregar variáveis de ambiente se existe .env
    if os.path.exists(".env"):
        from dotenv import load_dotenv

        load_dotenv()

    print("🏢 Inserindo menu de Estabelecimentos...")
    asyncio.run(insert_establishments_menu())
