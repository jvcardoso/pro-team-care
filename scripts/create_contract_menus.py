#!/usr/bin/env python3
"""
Script para criar estrutura de menus para contratos home care
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def create_contract_menus():
    print("=== CRIANDO MENUS DE CONTRATOS HOME CARE ===")

    try:
        async for db in get_db():
            # Define menu structure for contracts
            menus = [
                # Main Home Care Menu (if doesn't exist)
                {
                    "name": "Home Care",
                    "slug": "home-care",
                    "url": None,
                    "parent_id": None,
                    "level": 0,
                    "sort_order": 30,
                    "menu_type": "folder",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "homecare.access",
                    "company_specific": False,
                    "establishment_specific": True,
                    "icon": "Heart",
                    "description": "Sistema de Home Care",
                },
                # Contracts submenu
                {
                    "name": "Contratos",
                    "slug": "contratos",
                    "url": "/admin/contratos",
                    "parent_slug": "home-care",
                    "level": 1,
                    "sort_order": 10,
                    "menu_type": "page",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "contracts_view",
                    "company_specific": False,
                    "establishment_specific": False,
                    "icon": "FileText",
                    "description": "Gerenciar contratos home care",
                },
                # Medical Authorizations submenu
                {
                    "name": "Autorizações Médicas",
                    "slug": "autorizacoes-medicas",
                    "url": "/admin/autorizacoes-medicas",
                    "parent_slug": "home-care",
                    "level": 1,
                    "sort_order": 20,
                    "menu_type": "page",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "medical_authorizations_view",
                    "company_specific": False,
                    "establishment_specific": False,
                    "icon": "ClipboardCheck",
                    "description": "Gerenciar autorizações médicas",
                },
                # Service Executions submenu
                {
                    "name": "Execuções de Serviço",
                    "slug": "execucoes-servico",
                    "url": "/admin/execucoes-servico",
                    "parent_slug": "home-care",
                    "level": 1,
                    "sort_order": 30,
                    "menu_type": "page",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "service_executions_view",
                    "company_specific": False,
                    "establishment_specific": True,
                    "icon": "Activity",
                    "description": "Registrar e acompanhar execuções de serviços",
                },
                # Services Catalog submenu
                {
                    "name": "Catálogo de Serviços",
                    "slug": "catalogo-servicos",
                    "url": "/admin/catalogo-servicos",
                    "parent_slug": "home-care",
                    "level": 1,
                    "sort_order": 40,
                    "menu_type": "page",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "services_catalog_view",
                    "company_specific": False,
                    "establishment_specific": False,
                    "icon": "Package",
                    "description": "Catálogo de serviços disponíveis",
                },
                # Contract Reports submenu
                {
                    "name": "Relatórios de Contratos",
                    "slug": "relatorios-contratos",
                    "url": "/admin/relatorios-contratos",
                    "parent_slug": "home-care",
                    "level": 1,
                    "sort_order": 50,
                    "menu_type": "page",
                    "status": "active",
                    "is_visible": True,
                    "visible_in_menu": True,
                    "permission_name": "contract_reports_view",
                    "company_specific": False,
                    "establishment_specific": False,
                    "icon": "BarChart3",
                    "description": "Relatórios e análises de contratos",
                },
            ]

            # Process menus in order (parent first, then children)
            added_count = 0
            menu_ids = {}

            for menu in menus:
                # Handle parent_id resolution
                parent_id = None
                if menu.get("parent_slug"):
                    if menu["parent_slug"] in menu_ids:
                        parent_id = menu_ids[menu["parent_slug"]]
                    else:
                        # Look for existing parent
                        parent_query = text(
                            "SELECT id FROM master.menus WHERE slug = :slug AND deleted_at IS NULL"
                        )
                        parent_result = await db.execute(
                            parent_query, {"slug": menu["parent_slug"]}
                        )
                        parent = parent_result.fetchone()
                        if parent:
                            parent_id = parent.id
                            menu_ids[menu["parent_slug"]] = parent.id

                # Check if menu already exists
                check_query = text(
                    "SELECT id FROM master.menus WHERE slug = :slug AND deleted_at IS NULL"
                )
                result = await db.execute(check_query, {"slug": menu["slug"]})
                existing = result.fetchone()

                if not existing:
                    # Insert new menu
                    insert_query = text(
                        """
                        INSERT INTO master.menus
                        (name, slug, url, parent_id, level, sort_order, type, is_active,
                         is_visible, visible_in_menu, permission_name, company_specific,
                         establishment_specific, icon, description, created_at, updated_at)
                        VALUES (:name, :slug, :url, :parent_id, :level, :sort_order, :type,
                                :is_active, :is_visible, :visible_in_menu, :permission_name,
                                :company_specific, :establishment_specific, :icon, :description,
                                NOW(), NOW())
                        RETURNING id
                        """
                    )

                    menu_data = {
                        "name": menu["name"],
                        "slug": menu["slug"],
                        "url": menu["url"],
                        "parent_id": parent_id,
                        "level": menu["level"],
                        "sort_order": menu["sort_order"],
                        "type": menu["menu_type"],
                        "is_active": menu["status"] == "active",
                        "is_visible": menu["is_visible"],
                        "visible_in_menu": menu["visible_in_menu"],
                        "permission_name": menu["permission_name"],
                        "company_specific": menu["company_specific"],
                        "establishment_specific": menu["establishment_specific"],
                        "icon": menu["icon"],
                        "description": menu["description"],
                    }

                    result = await db.execute(insert_query, menu_data)
                    menu_id = result.fetchone()[0]
                    menu_ids[menu["slug"]] = menu_id
                    added_count += 1
                    print(f"✅ Menu criado: {menu['name']} (ID: {menu_id})")
                else:
                    menu_ids[menu["slug"]] = existing.id
                    print(f"⚠️ Menu já existe: {menu['name']} (ID: {existing.id})")

            if added_count > 0:
                await db.commit()
                print(f"\n🎉 {added_count} menus criados com sucesso!")
            else:
                print("\n✅ Todos os menus já existem no sistema!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


async def update_existing_client_menu():
    print("\n=== ATUALIZANDO MENU DE CLIENTES PARA INCLUIR CONTRATOS ===")

    try:
        async for db in get_db():
            # Check if clients menu exists
            check_query = text(
                "SELECT id FROM master.menus WHERE slug = 'clientes' AND deleted_at IS NULL"
            )
            result = await db.execute(check_query)
            clients_menu = result.fetchone()

            if clients_menu:
                # Update the description to mention contracts
                update_query = text(
                    """
                    UPDATE master.menus
                    SET description = 'Gerenciar clientes e seus contratos home care',
                        updated_at = NOW()
                    WHERE id = :menu_id
                    """
                )
                await db.execute(update_query, {"menu_id": clients_menu.id})
                await db.commit()
                print(
                    "✅ Menu de clientes atualizado para incluir referência aos contratos"
                )
            else:
                print("⚠️ Menu de clientes não encontrado")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


async def main():
    await create_contract_menus()
    await update_existing_client_menu()
    print("\n🎯 Estrutura de menus para contratos home care criada com sucesso!")
    print("\nPróximos passos:")
    print("1. ✅ Implementar as páginas frontend correspondentes")
    print("2. ✅ Integrar a aba de contratos na página de detalhes do cliente")
    print("3. ✅ Testar a navegação e permissões")


if __name__ == "__main__":
    asyncio.run(main())
