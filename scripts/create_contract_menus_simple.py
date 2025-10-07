#!/usr/bin/env python3
"""
Script simplificado para criar menus de contratos home care
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def create_contract_menus_simple():
    print("=== CRIANDO MENUS DE CONTRATOS HOME CARE (MODO SIMPLES) ===")

    try:
        async for db in get_db():
            # Home Care main menu should already exist (ID: 10)
            home_care_parent_id = 10

            # Define simple menu items to add under Home Care
            menus = [
                {
                    "name": "Contratos",
                    "slug": "contratos",
                    "url": "/admin/contratos",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 10,
                    "permission_name": "contracts_view",
                    "icon": "FileText",
                    "description": "Gerenciar contratos home care",
                },
                {
                    "name": "Autorizações Médicas",
                    "slug": "autorizacoes-medicas",
                    "url": "/admin/autorizacoes-medicas",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 20,
                    "permission_name": "medical_authorizations_view",
                    "icon": "ClipboardCheck",
                    "description": "Gerenciar autorizações médicas",
                },
                {
                    "name": "Execuções de Serviço",
                    "slug": "execucoes-servico",
                    "url": "/admin/execucoes-servico",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 30,
                    "permission_name": "service_executions_view",
                    "icon": "Activity",
                    "description": "Registrar e acompanhar execuções de serviços",
                },
                {
                    "name": "Catálogo de Serviços",
                    "slug": "catalogo-servicos",
                    "url": "/admin/catalogo-servicos",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 40,
                    "permission_name": "services_catalog_view",
                    "icon": "Package",
                    "description": "Catálogo de serviços disponíveis",
                },
                {
                    "name": "Relatórios de Contratos",
                    "slug": "relatorios-contratos",
                    "url": "/admin/relatorios-contratos",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 50,
                    "permission_name": "contract_reports_view",
                    "icon": "BarChart3",
                    "description": "Relatórios e análises de contratos",
                },
            ]

            added_count = 0
            for menu in menus:
                # Check if menu already exists
                check_query = text(
                    "SELECT id FROM master.menus WHERE slug = :slug AND deleted_at IS NULL"
                )
                result = await db.execute(check_query, {"slug": menu["slug"]})
                existing = result.fetchone()

                if not existing:
                    # Insert with minimal required fields
                    insert_query = text(
                        """
                        INSERT INTO master.menus
                        (name, slug, url, parent_id, level, sort_order, permission_name, icon, description)
                        VALUES (:name, :slug, :url, :parent_id, :level, :sort_order, :permission_name, :icon, :description)
                        """
                    )

                    await db.execute(insert_query, menu)
                    added_count += 1
                    print(f"✅ Menu criado: {menu['name']}")
                else:
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


async def main():
    await create_contract_menus_simple()
    print("\n🎯 Menus de contratos home care criados!")
    print("\nPróximos passos:")
    print("1. ✅ Implementar as páginas frontend correspondentes")
    print("2. ✅ Integrar a aba de contratos na página de detalhes do cliente")
    print("3. ✅ Testar a navegação e permissões")


if __name__ == "__main__":
    asyncio.run(main())
