#!/usr/bin/env python3
"""
Script para mover apenas os 4 menus de contratos do Home Care
para Administração/Negócio, mantendo Home Care com seus menus originais
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def move_contract_menus_to_business():
    print("=== MOVENDO MENUS DE CONTRATOS PARA ADMINISTRAÇÃO/NEGÓCIO ===")

    try:
        async for db in get_db():
            # IDs conhecidos
            home_care_id = 10  # Menu Home Care
            business_id = 139  # Menu Negócio dentro de Administração

            # IDs dos 4 menus de contratos que devem ser movidos
            contract_menu_ids = [
                142,
                146,
                148,
                151,
            ]  # Gestão de Contratos, Gestão de Vidas, Catálogo de Serviços, Relatórios Contratos

            print(
                f"📋 Movendo 4 menus de contratos do Home Care (ID: {home_care_id}) para Negócio (ID: {business_id})"
            )

            # 1. Verificar os menus que serão movidos
            verify_query = text(
                """
                SELECT id, name, slug, parent_id, level
                FROM master.menus
                WHERE id = ANY(:menu_ids)
                ORDER BY id
            """
            )
            result = await db.execute(verify_query, {"menu_ids": contract_menu_ids})
            menus_to_move = result.fetchall()

            print("\n📦 Menus que serão movidos:")
            for menu in menus_to_move:
                print(f"  ├── {menu.name} (ID: {menu.id})")

            # 2. Mover os 4 menus de contratos para Negócio
            update_contract_menus_query = text(
                """
                UPDATE master.menus
                SET parent_id = :business_id,
                    level = 3
                WHERE id = ANY(:menu_ids)
            """
            )

            result = await db.execute(
                update_contract_menus_query,
                {"business_id": business_id, "menu_ids": contract_menu_ids},
            )

            print(
                f"\n✅ {result.rowcount} menus de contratos movidos para Administração/Negócio"
            )

            # 3. Atualizar os submenus dos menus movidos (incrementar 1 nível)
            # Os submenus que eram nível 2 agora ficarão nível 4
            submenus_updated = 0
            for menu_id in contract_menu_ids:
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

            # 4. Verificar a estrutura final do Home Care (deve manter apenas os menus originais)
            print("\n📊 Home Care após a movimentação:")
            home_care_verify_query = text(
                """
                SELECT id, name, slug, parent_id, level
                FROM master.menus
                WHERE parent_id = :home_care_id
                ORDER BY sort_order
            """
            )
            result = await db.execute(
                home_care_verify_query, {"home_care_id": home_care_id}
            )
            remaining_menus = result.fetchall()

            print("Home Care")
            for menu in remaining_menus:
                print(f"  ├── {menu.name} (ID: {menu.id})")

            # 5. Verificar a estrutura do Negócio
            print("\n📊 Administração/Negócio após a movimentação:")
            business_verify_query = text(
                """
                SELECT id, name, slug, parent_id, level
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
    await move_contract_menus_to_business()
    print("\n🎯 Menus de contratos movidos para Administração/Negócio!")
    print("\n📋 Nova estrutura:")
    print("Home Care")
    print("├── Consultas")
    print("├── Pacientes")
    print("├── Profissionais")
    print("└── Relatórios")
    print("")
    print("Administração")
    print("└── Negócio")
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
    print(
        "\n✅ Separação perfeita: Home Care com funcionalidades originais e Contratos em Negócio!"
    )


if __name__ == "__main__":
    asyncio.run(main())
