#!/usr/bin/env python3
"""
Script completo para criar todos os menus de contratos home care
Baseado no PLANO_IMPLEMENTACAO_CONTRATOS_HOME_CARE.md
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def create_contract_menus_complete():
    print("=== CRIANDO SISTEMA COMPLETO DE MENUS - CONTRATOS HOME CARE ===")

    try:
        async for db in get_db():
            # Get next available ID
            next_id_query = text("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM master.menus")
            result = await db.execute(next_id_query)
            current_id = result.fetchone().next_id

            # Home Care main menu should already exist (ID: 10)
            home_care_parent_id = 10

            # Define complete menu structure based on implementation plan
            menus = [
                # === GESTÃO DE CONTRATOS ===
                {
                    "id": current_id,
                    "name": "Gestão de Contratos",
                    "slug": "gestao-contratos",
                    "url": "",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 10,
                    "permission_name": "contracts_menu",
                    "icon": "FileText",
                    "description": "Menu principal de gestão de contratos"
                },
                {
                    "id": current_id + 1,
                    "name": "Lista de Contratos",
                    "slug": "lista-contratos",
                    "url": "/admin/contratos",
                    "parent_id": current_id,
                    "level": 2,
                    "sort_order": 10,
                    "permission_name": "contracts_view",
                    "icon": "List",
                    "description": "Listar todos os contratos"
                },
                {
                    "id": current_id + 2,
                    "name": "Novo Contrato",
                    "slug": "novo-contrato",
                    "url": "/admin/contratos?action=create",
                    "parent_id": current_id,
                    "level": 2,
                    "sort_order": 20,
                    "permission_name": "contracts_create",
                    "icon": "Plus",
                    "description": "Criar novo contrato"
                },
                {
                    "id": current_id + 3,
                    "name": "Dashboard Contratos",
                    "slug": "dashboard-contratos",
                    "url": "/admin/contratos/dashboard",
                    "parent_id": current_id,
                    "level": 2,
                    "sort_order": 30,
                    "permission_name": "contract_dashboard_view",
                    "icon": "BarChart3",
                    "description": "Dashboard executivo de contratos"
                },

                # === GESTÃO DE VIDAS ===
                {
                    "id": current_id + 4,
                    "name": "Gestão de Vidas",
                    "slug": "gestao-vidas",
                    "url": "",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 20,
                    "permission_name": "contract_lives_menu",
                    "icon": "Users",
                    "description": "Menu de gestão de vidas dos contratos"
                },
                {
                    "id": current_id + 5,
                    "name": "Lista de Vidas Ativas",
                    "slug": "lista-vidas-ativas",
                    "url": "/admin/contratos/vidas",
                    "parent_id": current_id + 4,
                    "level": 2,
                    "sort_order": 10,
                    "permission_name": "contract_lives_view",
                    "icon": "UserCheck",
                    "description": "Visualizar vidas ativas dos contratos"
                },

                # === CATÁLOGO DE SERVIÇOS ===
                {
                    "id": current_id + 6,
                    "name": "Catálogo de Serviços",
                    "slug": "catalogo-servicos",
                    "url": "",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 30,
                    "permission_name": "services_catalog_menu",
                    "icon": "Package",
                    "description": "Menu do catálogo de serviços"
                },
                {
                    "id": current_id + 7,
                    "name": "Serviços Disponíveis",
                    "slug": "servicos-disponiveis",
                    "url": "/admin/servicos",
                    "parent_id": current_id + 6,
                    "level": 2,
                    "sort_order": 10,
                    "permission_name": "services_catalog_view",
                    "icon": "Package",
                    "description": "Visualizar catálogo de serviços disponíveis"
                },
                {
                    "id": current_id + 8,
                    "name": "Autorizações Médicas",
                    "slug": "autorizacoes-medicas",
                    "url": "/admin/autorizacoes",
                    "parent_id": current_id + 6,
                    "level": 2,
                    "sort_order": 20,
                    "permission_name": "medical_authorizations_view",
                    "icon": "ClipboardCheck",
                    "description": "Gerenciar autorizações médicas"
                },

                # === RELATÓRIOS ===
                {
                    "id": current_id + 9,
                    "name": "Relatórios Contratos",
                    "slug": "relatorios-contratos",
                    "url": "",
                    "parent_id": home_care_parent_id,
                    "level": 1,
                    "sort_order": 40,
                    "permission_name": "contract_reports_menu",
                    "icon": "BarChart3",
                    "description": "Menu de relatórios de contratos"
                },
                {
                    "id": current_id + 10,
                    "name": "Dashboard Executivo",
                    "slug": "dashboard-executivo",
                    "url": "/admin/relatorios",
                    "parent_id": current_id + 9,
                    "level": 2,
                    "sort_order": 10,
                    "permission_name": "executive_dashboard_view",
                    "icon": "TrendingUp",
                    "description": "Dashboard executivo de contratos"
                },
                {
                    "id": current_id + 11,
                    "name": "Relatórios Customizados",
                    "slug": "relatorios-customizados",
                    "url": "/admin/relatorios/customizados",
                    "parent_id": current_id + 9,
                    "level": 2,
                    "sort_order": 20,
                    "permission_name": "custom_reports_view",
                    "icon": "FileSpreadsheet",
                    "description": "Relatórios customizados de contratos"
                }
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
                    # Insert with all required fields including ID
                    insert_query = text(
                        """
                        INSERT INTO master.menus
                        (id, name, slug, url, parent_id, level, sort_order, permission_name, icon, description)
                        VALUES (:id, :name, :slug, :url, :parent_id, :level, :sort_order, :permission_name, :icon, :description)
                        """
                    )

                    await db.execute(insert_query, menu)
                    added_count += 1
                    print(f"✅ Menu criado: {menu['name']} (ID: {menu['id']})")
                else:
                    print(f"⚠️ Menu já existe: {menu['name']} (ID: {existing.id})")

            if added_count > 0:
                await db.commit()
                print(f"\n🎉 {added_count} menus criados com sucesso!")
                print(f"📊 IDs utilizados: {current_id} até {current_id + len(menus) - 1}")
            else:
                print("\n✅ Todos os menus já existem no sistema!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await create_contract_menus_complete()
    print("\n🎯 Sistema completo de menus de contratos home care criado!")
    print("\n📋 Estrutura criada:")
    print("├── Gestão de Contratos")
    print("│   ├── Lista de Contratos (/admin/contratos)")
    print("│   ├── Novo Contrato (/admin/contratos?action=create)")
    print("│   └── Dashboard Contratos (/admin/contratos/dashboard)")
    print("├── Gestão de Vidas")
    print("│   └── Lista de Vidas Ativas (/admin/contratos/vidas)")
    print("├── Catálogo de Serviços")
    print("│   ├── Serviços Disponíveis (/admin/servicos)")
    print("│   └── Autorizações Médicas (/admin/autorizacoes)")
    print("└── Relatórios Contratos")
    print("    ├── Dashboard Executivo (/admin/relatorios)")
    print("    └── Relatórios Customizados (/admin/relatorios/customizados)")
    print("\n✅ Próximos passos:")
    print("1. Verificar permissões correspondentes")
    print("2. Testar navegação no frontend")
    print("3. Ajustar URLs conforme necessário")


if __name__ == "__main__":
    asyncio.run(main())