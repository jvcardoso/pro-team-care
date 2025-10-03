#!/usr/bin/env python3
"""
Script para reverter Home Care para sua posição original (nível 0)
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def revert_homecare_position():
    print("=== REVERTENDO HOME CARE PARA POSIÇÃO ORIGINAL ===")

    try:
        async for db in get_db():
            home_care_id = 10  # Menu Home Care

            print(f"📋 Revertendo Home Care (ID: {home_care_id}) para posição original")

            # 1. Mover Home Care de volta para nível 0 (menu principal)
            update_homecare_query = text("""
                UPDATE master.menus
                SET parent_id = NULL,
                    level = 0,
                    sort_order = 10
                WHERE id = :home_care_id
            """)

            await db.execute(update_homecare_query, {
                "home_care_id": home_care_id
            })

            print("✅ Home Care restaurado como menu principal (nível 0)")

            # 2. Reverter os submenus de Home Care para nível 1
            update_submenus_level1_query = text("""
                UPDATE master.menus
                SET level = 1
                WHERE parent_id = :home_care_id AND level = 2
            """)

            result = await db.execute(update_submenus_level1_query, {
                "home_care_id": home_care_id
            })

            print(f"✅ {result.rowcount} submenus revertidos para nível 1")

            # 3. Reverter sub-submenus para nível 2
            # Primeiro, encontrar os IDs dos submenus de primeiro nível
            get_level1_menus_query = text("""
                SELECT id FROM master.menus
                WHERE parent_id = :home_care_id AND level = 1
            """)
            result = await db.execute(get_level1_menus_query, {"home_care_id": home_care_id})
            level1_menu_ids = [row.id for row in result.fetchall()]

            level2_updated = 0
            for menu_id in level1_menu_ids:
                update_level2_query = text("""
                    UPDATE master.menus
                    SET level = 2
                    WHERE parent_id = :menu_id AND level = 3
                """)
                result = await db.execute(update_level2_query, {"menu_id": menu_id})
                level2_updated += result.rowcount

            print(f"✅ {level2_updated} sub-submenus revertidos para nível 2")

            # 4. Verificar a estrutura final
            print("\n📊 Verificando estrutura restaurada:")

            verify_query = text("""
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
            """)

            result = await db.execute(verify_query, {"home_care_id": home_care_id})
            rows = result.fetchall()

            for row in rows:
                indent = "  " * row.level if row.level > 0 else ""
                print(f"{indent}├── {row.name} (ID: {row.id}, Level: {row.level}, Parent: {row.parent_id})")

            # Commit das alterações
            await db.commit()
            print("\n🎉 Reversão concluída com sucesso!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await revert_homecare_position()
    print("\n🎯 Home Care restaurado para posição original!")
    print("\n📋 Estrutura restaurada:")
    print("Home Care (Menu Principal)")
    print("├── Consultas")
    print("├── Pacientes")
    print("├── Profissionais")
    print("├── Relatórios")
    print("├── Gestão de Contratos")
    print("│   ├── Lista de Contratos")
    print("│   ├── Novo Contrato")
    print("│   └── Dashboard Contratos")
    print("├── Gestão de Vidas")
    print("│   └── Lista de Vidas Ativas")
    print("├── Catálogo de Serviços")
    print("│   ├── Serviços Disponíveis")
    print("│   └── Autorizações Médicas")
    print("└── Relatórios Contratos")
    print("    ├── Dashboard Executivo")
    print("    └── Relatórios Customizados")
    print("\n✅ Home Care está novamente como menu principal independente!")


if __name__ == "__main__":
    asyncio.run(main())