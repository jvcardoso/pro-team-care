#!/usr/bin/env python3
"""
Script para adicionar permissões do sistema de faturamento
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog
from sqlalchemy import text

from app.infrastructure.database import async_session

logger = structlog.get_logger()


async def add_billing_permissions():
    """Add billing system permissions to the database"""

    billing_permissions = [
        # Visualização de faturamento
        {
            "name": "billing_view",
            "display_name": "Visualizar Faturamento",
            "description": "Permite visualizar faturas, comprovantes e dados de faturamento",
            "module": "faturamento",
            "action": "read",
            "resource": "billing",
            "context_level": "company",
        },
        # Criação de faturas
        {
            "name": "billing_create",
            "display_name": "Criar Faturas",
            "description": "Permite criar faturas e configurar agendas de faturamento",
            "module": "faturamento",
            "action": "create",
            "resource": "billing",
            "context_level": "company",
        },
        # Atualização de faturas
        {
            "name": "billing_update",
            "display_name": "Atualizar Faturamento",
            "description": "Permite atualizar faturas, status de pagamento e dados de faturamento",
            "module": "faturamento",
            "action": "update",
            "resource": "billing",
            "context_level": "company",
        },
        # Aprovação de comprovantes
        {
            "name": "billing_approve",
            "display_name": "Aprovar Comprovantes",
            "description": "Permite aprovar ou rejeitar comprovantes de pagamento",
            "module": "faturamento",
            "action": "approve",
            "resource": "receipts",
            "context_level": "company",
        },
        # Administração completa de faturamento
        {
            "name": "billing_admin",
            "display_name": "Administrar Faturamento",
            "description": "Acesso completo ao sistema de faturamento e automação",
            "module": "faturamento",
            "action": "admin",
            "resource": "billing",
            "context_level": "company",
        },
        # Relatórios financeiros
        {
            "name": "billing_reports",
            "display_name": "Relatórios Financeiros",
            "description": "Permite gerar e visualizar relatórios financeiros e de cobrança",
            "module": "faturamento",
            "action": "read",
            "resource": "reports",
            "context_level": "company",
        },
        # Dashboard financeiro
        {
            "name": "billing_dashboard",
            "display_name": "Dashboard Financeiro",
            "description": "Permite visualizar métricas e dashboard financeiro",
            "module": "faturamento",
            "action": "read",
            "resource": "dashboard",
            "context_level": "company",
        },
    ]

    async with async_session() as db:
        try:
            # Check if permissions already exist
            for perm in billing_permissions:
                check_query = text(
                    """
                    SELECT id FROM master.permissions
                    WHERE name = :name
                """
                )
                result = await db.execute(check_query, {"name": perm["name"]})
                existing = result.fetchone()

                if existing:
                    logger.info(f"Permission {perm['name']} already exists, skipping")
                    continue

                # Insert new permission
                insert_query = text(
                    """
                    INSERT INTO master.permissions
                    (name, display_name, description, module, action, resource, context_level, is_active, created_at, updated_at)
                    VALUES
                    (:name, :display_name, :description, :module, :action, :resource, :context_level, true, NOW(), NOW())
                """
                )

                await db.execute(insert_query, perm)
                logger.info(
                    f"Added permission: {perm['name']} - {perm['display_name']}"
                )

            # Commit all changes
            await db.commit()
            logger.info("✅ All billing permissions added successfully!")

            # Now add permissions to existing roles
            await assign_billing_permissions_to_roles(db)

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error adding billing permissions: {e}")
            raise


async def assign_billing_permissions_to_roles(db):
    """Assign billing permissions to appropriate roles"""

    # Define role-permission mappings
    role_permissions = {
        "Administrador Geral": [
            "billing_view",
            "billing_create",
            "billing_update",
            "billing_approve",
            "billing_admin",
            "billing_reports",
            "billing_dashboard",
        ],
        "Administrador da Empresa": [
            "billing_view",
            "billing_create",
            "billing_update",
            "billing_approve",
            "billing_admin",
            "billing_reports",
            "billing_dashboard",
        ],
        "Gestor Financeiro": [
            "billing_view",
            "billing_create",
            "billing_update",
            "billing_approve",
            "billing_reports",
            "billing_dashboard",
        ],
        "Supervisor": ["billing_view", "billing_update", "billing_dashboard"],
        "Operador": ["billing_view"],
        "Assistente Administrativo": [
            "billing_view",
            "billing_create",
            "billing_update",
        ],
    }

    try:
        for role_name, permissions in role_permissions.items():
            # Get role ID
            role_query = text("SELECT id FROM master.roles WHERE name = :name")
            role_result = await db.execute(role_query, {"name": role_name})
            role = role_result.fetchone()

            if not role:
                logger.warning(f"Role '{role_name}' not found, skipping")
                continue

            role_id = role.id

            for perm_code in permissions:
                # Get permission ID
                perm_query = text(
                    "SELECT id FROM master.permissions WHERE name = :name"
                )
                perm_result = await db.execute(perm_query, {"name": perm_code})
                perm = perm_result.fetchone()

                if not perm:
                    logger.warning(f"Permission '{perm_code}' not found, skipping")
                    continue

                permission_id = perm.id

                # Check if role-permission already exists
                check_query = text(
                    """
                    SELECT id FROM master.role_permissions
                    WHERE role_id = :role_id AND permission_id = :permission_id
                """
                )
                existing = await db.execute(
                    check_query, {"role_id": role_id, "permission_id": permission_id}
                )

                if existing.fetchone():
                    continue  # Already exists

                # Add role-permission
                insert_query = text(
                    """
                    INSERT INTO master.role_permissions
                    (role_id, permission_id, granted_at)
                    VALUES (:role_id, :permission_id, NOW())
                """
                )

                await db.execute(
                    insert_query, {"role_id": role_id, "permission_id": permission_id}
                )

                logger.info(f"Assigned {perm_code} to {role_name}")

        await db.commit()
        logger.info("✅ Billing permissions assigned to roles successfully!")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error assigning permissions to roles: {e}")
        raise


async def show_billing_permissions_summary():
    """Show summary of billing permissions"""

    async with async_session() as db:
        try:
            # Get all billing permissions
            query = text(
                """
                SELECT p.name, p.display_name, p.description, p.module,
                       COUNT(rp.id) as role_count
                FROM master.permissions p
                LEFT JOIN master.role_permissions rp ON p.id = rp.permission_id
                WHERE p.module = 'faturamento'
                GROUP BY p.id, p.name, p.display_name, p.description, p.module
                ORDER BY p.name
            """
            )

            result = await db.execute(query)
            permissions = result.fetchall()

            print("\n" + "=" * 80)
            print("📊 BILLING PERMISSIONS SUMMARY")
            print("=" * 80)

            for perm in permissions:
                print(f"🔑 {perm.name}")
                print(f"   Display Name: {perm.display_name}")
                print(f"   Description: {perm.description}")
                print(f"   Assigned to {perm.role_count} roles")
                print()

            # Get roles with billing permissions
            roles_query = text(
                """
                SELECT r.name, COUNT(rp.id) as billing_perms_count
                FROM master.roles r
                JOIN master.role_permissions rp ON r.id = rp.role_id
                JOIN master.permissions p ON rp.permission_id = p.id
                WHERE p.module = 'faturamento'
                GROUP BY r.id, r.name
                ORDER BY billing_perms_count DESC, r.name
            """
            )

            roles_result = await db.execute(roles_query)
            roles = roles_result.fetchall()

            print("👥 ROLES WITH BILLING PERMISSIONS:")
            print("-" * 40)
            for role in roles:
                print(f"• {role.name}: {role.billing_perms_count} permissions")

            print("\n✅ Billing system permissions are properly configured!")

        except Exception as e:
            logger.error(f"❌ Error showing permissions summary: {e}")


if __name__ == "__main__":

    async def main():
        print("🚀 Adding billing system permissions...")
        await add_billing_permissions()
        await show_billing_permissions_summary()
        print("🎯 Billing permissions setup completed!")

    asyncio.run(main())
