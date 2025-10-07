#!/usr/bin/env python3
"""
Script para mover Home Care para Administração/Negócio
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def move_homecare_to_business():
    print("=== MOVENDO HOME CARE PARA ADMINISTRAÇÃO/NEGÓCIO ===")

    try:
        async for db in get_db():
            # IDs conhecidos
            home_care_id = 10  # Menu Home Care atual
            business_id = 139  # Menu Negócio dentro de Administração

            print(
                f"📋 Movendo Home Care (ID: {home_care_id}) para Negócio (ID: {business_id})"
            )

            # 1. Primeiro, vamos mover o Home Care para ser submenu de Negócio
            update_homecare_query = text(
                """
                UPDATE master.menus
                SET parent_id = :business_id,
                    level = 3,
                    sort_order = 10
                WHERE id = :home_care_id
            """
            )

            await db.execute(
                update_homecare_query,
                {"business_id": business_id, "home_care_id": home_care_id},
            )

            print("✅ Home Care movido para Administração/Negócio")

            # 2. Atualizar os níveis dos submenus de Home Care (incrementar 1 nível)
            # Os menus que tinham level 1 agora ficarão level 2
            # Os menus que tinham level 2 agora ficarão level 3

            update_submenus_level1_query = text(
                """
                UPDATE master.menus
                SET level = 2
                WHERE parent_id = :home_care_id AND level = 1
            """
            )

            await db.execute(
                update_submenus_level1_query, {"home_care_id": home_care_id}
            )

            # Verificar quantos foram atualizados
            check_level1_query = text(
                """
                SELECT COUNT(*) as count
                FROM master.menus
                WHERE parent_id = :home_care_id AND level = 2
            """
            )
            result = await db.execute(
                check_level1_query, {"home_care_id": home_care_id}
            )
            level1_count = result.fetchone().count

            print(f"✅ {level1_count} submenus de nível 1 atualizados para nível 2")

            # 3. Atualizar submenus de nível 2 para nível 3
            # Primeiro, encontrar os IDs dos submenus de primeiro nível
            get_level1_menus_query = text(
                """
                SELECT id FROM master.menus
                WHERE parent_id = :home_care_id AND level = 2
            """
            )
            result = await db.execute(
                get_level1_menus_query, {"home_care_id": home_care_id}
            )
            level1_menu_ids = [row.id for row in result.fetchall()]

            level2_updated = 0
            for menu_id in level1_menu_ids:
                update_level2_query = text(
                    """
                    UPDATE master.menus
                    SET level = 3
                    WHERE parent_id = :menu_id AND level = 2
                """
                )
                result = await db.execute(update_level2_query, {"menu_id": menu_id})
                level2_updated += result.rowcount

            print(f"✅ {level2_updated} submenus de nível 2 atualizados para nível 3")

            # 4. Verificar a estrutura final
            print("\n📊 Verificando estrutura final:")

            verify_query = text(
                """
                SELECT id, name, slug, parent_id, level, sort_order
                FROM master.menus
                WHERE id = :home_care_id
                   OR parent_id = :home_care_id
                   OR parent_id IN (
                       SELECT id FROM master.menus WHERE parent_id = :home_care_id
                   )
                ORDER BY
                    CASE WHEN id = :home_care_id THEN 0 ELSE 1 END,
                    parent_id,
                    sort_order
            """
            )

            result = await db.execute(verify_query, {"home_care_id": home_care_id})
            rows = result.fetchall()

            for row in rows:
                indent = "  " * (row.level - 3) if row.level >= 3 else ""
                print(
                    f"{indent}├── {row.name} (ID: {row.id}, Level: {row.level}, Parent: {row.parent_id})"
                )

            # Commit das alterações
            await db.commit()
            print("\n🎉 Migração concluída com sucesso!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


async def main():
    await move_homecare_to_business()
    print("\n🎯 Home Care movido para Administração/Negócio!")
    print("\n📋 Nova estrutura:")
    print("Administração")
    print("└── Negócio")
    print("    └── Home Care")
    print("        ├── Gestão de Contratos")
    print("        ├── Gestão de Vidas")
    print("        ├── Catálogo de Serviços")
    print("        └── Relatórios Contratos")
    print("\n✅ Agora o Home Care está organizado dentro da seção de negócios!")


if __name__ == "__main__":
    asyncio.run(main())
