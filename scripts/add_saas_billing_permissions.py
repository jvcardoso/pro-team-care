#!/usr/bin/env python3
"""
Script para adicionar permissões do sistema SaaS Billing
Execução: python scripts/add_saas_billing_permissions.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from config.settings import settings

# Database URL
DATABASE_URL = f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_database}"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def add_saas_billing_permissions():
    """Adicionar permissões para o sistema SaaS Billing"""
    async with SessionLocal() as session:
        try:
            print("🔧 Adicionando permissões SaaS Billing...")

            # Definir as novas permissões SaaS
            saas_permissions = [
                # Visualização
                ("saas_billing_view", "Visualizar SaaS Billing", "Visualizar faturas e assinaturas SaaS", "system"),
                ("saas_billing_dashboard", "Dashboard SaaS Billing", "Acessar dashboard de métricas SaaS", "system"),
                ("saas_billing_reports", "Relatórios SaaS Billing", "Gerar relatórios de receita SaaS", "system"),

                # Gestão de Assinaturas
                ("saas_billing_create", "Criar Assinaturas SaaS", "Criar novas assinaturas de empresas", "system"),
                ("saas_billing_update", "Atualizar Assinaturas SaaS", "Atualizar assinaturas existentes", "system"),
                ("saas_billing_cancel", "Cancelar Assinaturas SaaS", "Cancelar assinaturas de empresas", "system"),

                # Pagamentos
                ("saas_billing_payment", "Processar Pagamentos SaaS", "Processar pagamentos de faturas SaaS", "system"),
                ("saas_billing_recurrent", "Cobrança Recorrente SaaS", "Configurar e gerenciar cobrança recorrente", "system"),
                ("saas_billing_automatic", "Faturamento Automático SaaS", "Executar faturamento automático", "system"),

                # Administração
                ("saas_billing_admin", "Administrar SaaS Billing", "Administração completa do billing SaaS", "system"),
            ]

            # Inserir permissões se não existirem
            permission_count = 0
            for code, name, description, context in saas_permissions:
                # Verificar se a permissão já existe
                result = await session.execute(
                    text("SELECT id FROM master.permissions WHERE code = :code"),
                    {"code": code}
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    await session.execute(
                        text("""
                            INSERT INTO master.permissions (code, name, description, context, is_active, created_at)
                            VALUES (:code, :name, :description, :context, true, NOW())
                        """),
                        {
                            "code": code,
                            "name": name,
                            "description": description,
                            "context": context
                        }
                    )
                    permission_count += 1
                    print(f"  ✅ Permissão adicionada: {code}")
                else:
                    print(f"  ⚠️  Permissão já existe: {code}")

            # Criar role 'saas_admin' se não existir
            result = await session.execute(
                text("SELECT id FROM master.roles WHERE name = 'saas_admin'"),
            )
            saas_admin_role = result.scalar_one_or_none()

            if not saas_admin_role:
                await session.execute(
                    text("""
                        INSERT INTO master.roles (name, description, is_active, created_at)
                        VALUES ('saas_admin', 'Administrador SaaS Billing', true, NOW())
                    """)
                )
                # Obter o ID da role criada
                result = await session.execute(
                    text("SELECT id FROM master.roles WHERE name = 'saas_admin'"),
                )
                saas_admin_role = result.scalar_one()
                print("  ✅ Role 'saas_admin' criada")
            else:
                print("  ⚠️  Role 'saas_admin' já existe")

            # Associar todas as permissões SaaS à role saas_admin
            permissions_added = 0
            for code, _, _, _ in saas_permissions:
                # Obter ID da permissão
                result = await session.execute(
                    text("SELECT id FROM master.permissions WHERE code = :code"),
                    {"code": code}
                )
                permission_id = result.scalar_one()

                # Verificar se a associação já existe
                result = await session.execute(
                    text("""
                        SELECT id FROM master.role_permissions
                        WHERE role_id = :role_id AND permission_id = :permission_id
                    """),
                    {"role_id": saas_admin_role, "permission_id": permission_id}
                )
                existing_association = result.scalar_one_or_none()

                if not existing_association:
                    await session.execute(
                        text("""
                            INSERT INTO master.role_permissions (role_id, permission_id, created_at)
                            VALUES (:role_id, :permission_id, NOW())
                        """),
                        {"role_id": saas_admin_role, "permission_id": permission_id}
                    )
                    permissions_added += 1

            print(f"  ✅ {permissions_added} permissões associadas à role 'saas_admin'")

            # Dar permissões SaaS ao usuário admin (se existir)
            result = await session.execute(
                text("SELECT id FROM master.users WHERE email = 'admin@proteamcare.com'"),
            )
            admin_user = result.scalar_one_or_none()

            if admin_user:
                # Verificar se o usuário já tem a role saas_admin
                result = await session.execute(
                    text("""
                        SELECT id FROM master.user_roles
                        WHERE user_id = :user_id AND role_id = :role_id
                    """),
                    {"user_id": admin_user, "role_id": saas_admin_role}
                )
                existing_user_role = result.scalar_one_or_none()

                if not existing_user_role:
                    await session.execute(
                        text("""
                            INSERT INTO master.user_roles (user_id, role_id, assigned_at, assigned_by)
                            VALUES (:user_id, :role_id, NOW(), :user_id)
                        """),
                        {"user_id": admin_user, "role_id": saas_admin_role}
                    )
                    print("  ✅ Role 'saas_admin' atribuída ao usuário admin")
                else:
                    print("  ⚠️  Usuário admin já possui role 'saas_admin'")
            else:
                print("  ⚠️  Usuário admin não encontrado")

            await session.commit()

            print(f"\n🎉 Processo concluído!")
            print(f"   📊 {permission_count} novas permissões adicionadas")
            print(f"   🔐 Role 'saas_admin' configurada")
            print(f"   👤 Permissões atribuídas ao usuário admin")
            print(f"\n📝 Permissões SaaS disponíveis:")
            for code, name, _, _ in saas_permissions:
                print(f"   • {code}: {name}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Erro ao adicionar permissões SaaS: {e}")
            raise
        finally:
            await session.close()


async def main():
    """Função principal"""
    print("🚀 Iniciando adição de permissões SaaS Billing...")

    try:
        await add_saas_billing_permissions()
        print("\n✅ Permissões SaaS Billing adicionadas com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())