#!/usr/bin/env python3
"""
Script para adicionar permissões específicas de contratos home care
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def add_contract_permissions():
    print("=== ADICIONANDO PERMISSÕES DE CONTRATOS HOME CARE ===")

    try:
        async for db in get_db():
            # Define contract-specific permissions
            contract_permissions = [
                # Contract Management
                {
                    "name": "contracts_create",
                    "display_name": "Criar Contratos",
                    "description": "Permite criar novos contratos home care",
                    "module": "contracts",
                    "action": "create",
                    "resource": "contracts",
                    "context_level": "company"
                },
                {
                    "name": "contracts_view",
                    "display_name": "Visualizar Contratos",
                    "description": "Permite visualizar contratos home care",
                    "module": "contracts",
                    "action": "view",
                    "resource": "contracts",
                    "context_level": "company"
                },
                {
                    "name": "contracts_update",
                    "display_name": "Atualizar Contratos",
                    "description": "Permite atualizar contratos home care",
                    "module": "contracts",
                    "action": "update",
                    "resource": "contracts",
                    "context_level": "company"
                },
                {
                    "name": "contracts_delete",
                    "display_name": "Excluir Contratos",
                    "description": "Permite excluir contratos home care",
                    "module": "contracts",
                    "action": "delete",
                    "resource": "contracts",
                    "context_level": "company"
                },

                # Contract Lives Management
                {
                    "name": "contract_lives_create",
                    "display_name": "Adicionar Vidas ao Contrato",
                    "description": "Permite adicionar vidas aos contratos",
                    "module": "contracts",
                    "action": "create",
                    "resource": "contract_lives",
                    "context_level": "company"
                },
                {
                    "name": "contract_lives_view",
                    "display_name": "Visualizar Vidas do Contrato",
                    "description": "Permite visualizar vidas vinculadas aos contratos",
                    "module": "contracts",
                    "action": "view",
                    "resource": "contract_lives",
                    "context_level": "company"
                },
                {
                    "name": "contract_lives_update",
                    "display_name": "Atualizar Vidas do Contrato",
                    "description": "Permite atualizar vidas dos contratos",
                    "module": "contracts",
                    "action": "update",
                    "resource": "contract_lives",
                    "context_level": "company"
                },
                {
                    "name": "contract_lives_delete",
                    "display_name": "Remover Vidas do Contrato",
                    "description": "Permite remover vidas dos contratos",
                    "module": "contracts",
                    "action": "delete",
                    "resource": "contract_lives",
                    "context_level": "company"
                },

                # Medical Authorizations
                {
                    "name": "medical_authorizations_create",
                    "display_name": "Criar Autorizações Médicas",
                    "description": "Permite criar autorizações médicas para serviços",
                    "module": "medical",
                    "action": "create",
                    "resource": "authorizations",
                    "context_level": "company"
                },
                {
                    "name": "medical_authorizations_view",
                    "display_name": "Visualizar Autorizações Médicas",
                    "description": "Permite visualizar autorizações médicas",
                    "module": "medical",
                    "action": "view",
                    "resource": "authorizations",
                    "context_level": "company"
                },
                {
                    "name": "medical_authorizations_update",
                    "display_name": "Atualizar Autorizações Médicas",
                    "description": "Permite atualizar autorizações médicas",
                    "module": "medical",
                    "action": "update",
                    "resource": "authorizations",
                    "context_level": "company"
                },
                {
                    "name": "medical_authorizations_cancel",
                    "display_name": "Cancelar Autorizações Médicas",
                    "description": "Permite cancelar autorizações médicas",
                    "module": "medical",
                    "action": "cancel",
                    "resource": "authorizations",
                    "context_level": "company"
                },

                # Service Executions
                {
                    "name": "service_executions_create",
                    "display_name": "Registrar Execução de Serviços",
                    "description": "Permite registrar execução de serviços home care",
                    "module": "services",
                    "action": "create",
                    "resource": "executions",
                    "context_level": "establishment"
                },
                {
                    "name": "service_executions_view",
                    "display_name": "Visualizar Execuções de Serviços",
                    "description": "Permite visualizar execuções de serviços",
                    "module": "services",
                    "action": "view",
                    "resource": "executions",
                    "context_level": "establishment"
                },
                {
                    "name": "service_executions_update",
                    "display_name": "Atualizar Execuções de Serviços",
                    "description": "Permite atualizar execuções de serviços",
                    "module": "services",
                    "action": "update",
                    "resource": "executions",
                    "context_level": "establishment"
                },
                {
                    "name": "service_executions_cancel",
                    "display_name": "Cancelar Execuções de Serviços",
                    "description": "Permite cancelar execuções de serviços",
                    "module": "services",
                    "action": "cancel",
                    "resource": "executions",
                    "context_level": "establishment"
                },

                # Services Catalog
                {
                    "name": "services_catalog_view",
                    "display_name": "Visualizar Catálogo de Serviços",
                    "description": "Permite visualizar catálogo de serviços home care",
                    "module": "services",
                    "action": "view",
                    "resource": "catalog",
                    "context_level": "company"
                },
                {
                    "name": "services_catalog_manage",
                    "display_name": "Gerenciar Catálogo de Serviços",
                    "description": "Permite gerenciar catálogo de serviços home care",
                    "module": "services",
                    "action": "manage",
                    "resource": "catalog",
                    "context_level": "company"
                },

                # Contract Reports
                {
                    "name": "contract_reports_view",
                    "display_name": "Visualizar Relatórios de Contratos",
                    "description": "Permite visualizar relatórios de contratos",
                    "module": "reports",
                    "action": "view",
                    "resource": "contracts",
                    "context_level": "company"
                },
                {
                    "name": "contract_reports_export",
                    "display_name": "Exportar Relatórios de Contratos",
                    "description": "Permite exportar relatórios de contratos",
                    "module": "reports",
                    "action": "export",
                    "resource": "contracts",
                    "context_level": "company"
                },

                # Financial
                {
                    "name": "contracts_financial_view",
                    "display_name": "Visualizar Financeiro de Contratos",
                    "description": "Permite visualizar informações financeiras dos contratos",
                    "module": "financial",
                    "action": "view",
                    "resource": "contracts",
                    "context_level": "company"
                },
                {
                    "name": "contracts_financial_manage",
                    "display_name": "Gerenciar Financeiro de Contratos",
                    "description": "Permite gerenciar informações financeiras dos contratos",
                    "module": "financial",
                    "action": "manage",
                    "resource": "contracts",
                    "context_level": "company"
                },
            ]

            # Insert permissions that don't exist
            added_count = 0
            for permission in contract_permissions:
                # Check if permission already exists
                check_query = text(
                    "SELECT id FROM master.permissions WHERE name = :name"
                )
                result = await db.execute(check_query, {"name": permission["name"]})
                existing = result.fetchone()

                if not existing:
                    # Insert new permission
                    insert_query = text(
                        """
                        INSERT INTO master.permissions
                        (name, display_name, description, module, action, resource, context_level, is_active)
                        VALUES (:name, :display_name, :description, :module, :action, :resource, :context_level, true)
                        """
                    )
                    await db.execute(insert_query, permission)
                    added_count += 1
                    print(f"✅ Adicionada permissão: {permission['name']}")
                else:
                    print(f"⚠️ Permissão já existe: {permission['name']}")

            if added_count > 0:
                await db.commit()
                print(f"\n🎉 {added_count} permissões adicionadas com sucesso!")
            else:
                print("\n✅ Todas as permissões de contratos já existem no sistema!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def assign_permissions_to_admin_role():
    print("\n=== ATRIBUINDO PERMISSÕES AO ROLE DE ADMIN ===")

    try:
        async for db in get_db():
            # Get all contract-related permissions
            permissions_query = text(
                """
                SELECT id, name FROM master.permissions
                WHERE name LIKE 'contract%' OR name LIKE 'medical_authorization%'
                   OR name LIKE 'service_execution%' OR name LIKE 'services_catalog%'
                ORDER BY name
                """
            )
            permissions_result = await db.execute(permissions_query)
            permissions = permissions_result.fetchall()

            # Get super_admin role
            role_query = text(
                "SELECT id FROM master.roles WHERE name = 'super_admin' AND is_active = true"
            )
            role_result = await db.execute(role_query)
            admin_role = role_result.fetchone()

            if not admin_role:
                print("❌ Role 'super_admin' não encontrado!")
                return

            # Assign permissions to admin role
            assigned_count = 0
            for permission in permissions:
                # Check if permission is already assigned
                check_query = text(
                    """
                    SELECT id FROM master.role_permissions
                    WHERE role_id = :role_id AND permission_id = :permission_id
                    """
                )
                result = await db.execute(check_query, {
                    "role_id": admin_role.id,
                    "permission_id": permission.id
                })
                existing = result.fetchone()

                if not existing:
                    # Assign permission to role
                    assign_query = text(
                        """
                        INSERT INTO master.role_permissions (role_id, permission_id, granted_at)
                        VALUES (:role_id, :permission_id, NOW())
                        """
                    )
                    await db.execute(assign_query, {
                        "role_id": admin_role.id,
                        "permission_id": permission.id
                    })
                    assigned_count += 1
                    print(f"✅ Atribuída ao admin: {permission.name}")
                else:
                    print(f"⚠️ Já atribuída ao admin: {permission.name}")

            if assigned_count > 0:
                await db.commit()
                print(f"\n🎉 {assigned_count} permissões atribuídas ao role admin!")
            else:
                print("\n✅ Todas as permissões já estavam atribuídas ao admin!")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def main():
    await add_contract_permissions()
    await assign_permissions_to_admin_role()


if __name__ == "__main__":
    asyncio.run(main())