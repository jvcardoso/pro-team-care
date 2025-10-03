#!/usr/bin/env python3
"""
Script para verificar a estrutura da tabela menus
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def check_menu_structure():
    print("=== VERIFICANDO ESTRUTURA DA TABELA MENUS ===")

    try:
        async for db in get_db():
            # Check table structure
            structure_query = text(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'master' AND table_name = 'menus'
                ORDER BY ordinal_position
                """
            )
            result = await db.execute(structure_query)
            columns = result.fetchall()

            print("📋 Estrutura da tabela master.menus:")
            for col in columns:
                print(f"   - {col.column_name}: {col.data_type} (Nullable: {col.is_nullable})")

            # Check if menu_type exists
            menu_type_exists = any(col.column_name == 'menu_type' for col in columns)
            print(f"\n🔍 Campo 'menu_type' existe: {'✅ SIM' if menu_type_exists else '❌ NÃO'}")

            # Show some existing menus
            print("\n📝 Alguns menus existentes:")
            sample_query = text(
                "SELECT id, name, slug, parent_id, level FROM master.menus WHERE deleted_at IS NULL LIMIT 5"
            )
            sample_result = await db.execute(sample_query)
            sample_menus = sample_result.fetchall()

            for menu in sample_menus:
                print(f"   - ID {menu.id}: {menu.name} (slug: {menu.slug}, level: {menu.level})")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_menu_structure())