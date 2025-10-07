#!/usr/bin/env python3
"""
Script para mover Empresas, Estabelecimentos e Clientes para Administração/Negócio
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def move_business_menus_to_negocio():
    print("=== MOVENDO EMPRESAS, ESTABELECIMENTOS E CLIENTES PARA NEGÓCIO ===")

    try:
        async for db in get_db():
            # IDs conhecidos
            business_id = 139  # Menu Negócio dentro de Administração

            # IDs dos menus que devem ser movidos
            menu_ids_to_move = [14, 136, 138]  # Empresas, Estabelecimentos, Clientes

            print(f"📋 Movendo 3 menus para Negócio (ID: {business_id})")

            # 1. Verificar os menus que serão movidos
            verify_query = text(
                """
                SELECT id, name, slug, parent_id, level
                FROM master.menus
                WHERE id = ANY(:menu_ids)
                ORDER BY id
            """
            )
            result = await db.execute(verify_query, {"menu_ids": menu_ids_to_move})
            menus_to_move = result.fetchall()

            print("\n📦 Menus que serão movidos:")
            for menu in menus_to_move:
                print(f"  ├── {menu.name} (ID: {menu.id})")

            # 2. Mover os 3 menus para Negócio
            update_menus_query = text(
                """
                UPDATE master.menus
                SET parent_id = :business_id,
                    level = 3
                WHERE id = ANY(:menu_ids)
            """
            )

            result = await db.execute(
                update_menus_query,
                {"business_id": business_id, "menu_ids": menu_ids_to_move},
            )

            print(f"\n✅ {result.rowcount} menus movidos para Administração/Negócio")

            # 3. Atualizar os submenus dos menus movidos (incrementar 1 nível)
            # Os submenus que eram nível 2 agora ficarão nível 4
            submenus_updated = 0
            for menu_id in menu_ids_to_move:
                update_submenus_query = text(
                    """
                    UPDATE master.menus
                    SET level = 4
                    WHERE parent_id = :menu_id AND level = 2
                """
                )
                result = await db.execute(update_submenus_query, {"menu_id": menu_id})
                submenus_updated += result.rowcount

            print(f"✅ {submenus_updated} submenus atualizados para nível 4")

            # 4. Verificar a estrutura final do Negócio
            print("\n📊 Administração/Negócio após a movimentação:")
            business_verify_query = text(
                """
                SELECT id, name, slug, parent_id, level, sort_order
                FROM master.menus
                WHERE parent_id = :business_id
                   OR parent_id IN (SELECT id FROM master.menus WHERE parent_id = :business_id)
                ORDER BY parent_id, sort_order
            """
            )
            result = await db.execute(
                business_verify_query, {"business_id": business_id}
            )
            business_menus = result.fetchall()

            print("Administração > Negócio")
            current_parent = None
            for menu in business_menus:
                if menu.parent_id == business_id:
                    current_parent = menu.id
                    print(f"  ├── {menu.name} (ID: {menu.id})")
                else:
                    print(f"    ├── {menu.name} (ID: {menu.id})")

            # Commit das alterações
            await db.commit()
            print("\n🎉 Movimentação concluída com sucesso!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


async def main():
    await move_business_menus_to_negocio()
    print("\n🎯 Menus de negócio organizados em Administração/Negócio!")
    print("\n📋 Nova estrutura completa:")
    print("Administração")
    print("└── Negócio")
    print("    ├── Empresas")
    print("    │   └── [submenus de empresas]")
    print("    ├── Estabelecimentos")
    print("    │   └── [submenus de estabelecimentos]")
    print("    ├── Clientes")
    print("    │   └── [submenus de clientes]")
    print("    ├── Gestão de Contratos")
    print("    │   ├── Lista de Contratos")
    print("    │   ├── Novo Contrato")
    print("    │   └── Dashboard Contratos")
    print("    ├── Gestão de Vidas")
    print("    │   └── Lista de Vidas Ativas")
    print("    ├── Catálogo de Serviços")
    print("    │   ├── Serviços Disponíveis")
    print("    │   └── Autorizações Médicas")
    print("    └── Relatórios Contratos")
    print("        ├── Dashboard Executivo")
    print("        └── Relatórios Customizados")
    print("\n✅ Organização completa: Todos os menus de negócio centralizados!")


if __name__ == "__main__":
    asyncio.run(main())
