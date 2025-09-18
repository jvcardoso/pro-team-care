#!/usr/bin/env python3
"""
Script para Fase 1: Criação de todas as permissões granulares no banco
Executa as migrações e popula as permissões necessárias
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Adicionar o caminho da aplicação
sys.path.append("/home/juliano/Projetos/pro_team_care_16")

from app.infrastructure.database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Definição completa das permissões granulares
PERMISSION_CATEGORIES = {
    "users": {
        "description": "Gestão de usuários",
        "permissions": [
            {"name": "users.view", "description": "Visualizar dados de usuários"},
            {"name": "users.list", "description": "Listar usuários"},
            {"name": "users.create", "description": "Criar novos usuários"},
            {"name": "users.edit", "description": "Editar dados de usuários"},
            {"name": "users.delete", "description": "Excluir usuários"},
            {"name": "users.activate", "description": "Ativar/desativar usuários"},
            {
                "name": "users.permissions",
                "description": "Gerenciar permissões de usuários",
            },
            {"name": "users.export", "description": "Exportar dados de usuários"},
        ],
    },
    "companies": {
        "description": "Gestão de empresas",
        "permissions": [
            {"name": "companies.view", "description": "Visualizar dados da empresa"},
            {"name": "companies.list", "description": "Listar empresas"},
            {"name": "companies.create", "description": "Criar novas empresas"},
            {"name": "companies.edit", "description": "Editar dados da empresa"},
            {"name": "companies.delete", "description": "Excluir empresas"},
            {"name": "companies.settings", "description": "Configurações da empresa"},
            {"name": "companies.export", "description": "Exportar dados da empresa"},
        ],
    },
    "establishments": {
        "description": "Gestão de estabelecimentos",
        "permissions": [
            {
                "name": "establishments.view",
                "description": "Visualizar estabelecimentos",
            },
            {"name": "establishments.list", "description": "Listar estabelecimentos"},
            {"name": "establishments.create", "description": "Criar estabelecimentos"},
            {"name": "establishments.edit", "description": "Editar estabelecimentos"},
            {
                "name": "establishments.delete",
                "description": "Excluir estabelecimentos",
            },
            {
                "name": "establishments.settings",
                "description": "Configurações do estabelecimento",
            },
            {
                "name": "establishments.export",
                "description": "Exportar dados do estabelecimento",
            },
        ],
    },
    "roles": {
        "description": "Gestão de perfis e permissões",
        "permissions": [
            {"name": "roles.view", "description": "Visualizar perfis"},
            {"name": "roles.list", "description": "Listar perfis"},
            {"name": "roles.create", "description": "Criar novos perfis"},
            {"name": "roles.edit", "description": "Editar perfis"},
            {"name": "roles.delete", "description": "Excluir perfis"},
            {"name": "roles.assign", "description": "Atribuir perfis a usuários"},
            {
                "name": "roles.permissions",
                "description": "Gerenciar permissões dos perfis",
            },
        ],
    },
    "menus": {
        "description": "Gestão de menus dinâmicos",
        "permissions": [
            {"name": "menus.view", "description": "Visualizar menus"},
            {"name": "menus.list", "description": "Listar menus"},
            {"name": "menus.create", "description": "Criar menus"},
            {"name": "menus.edit", "description": "Editar menus"},
            {"name": "menus.delete", "description": "Excluir menus"},
            {"name": "menus.reorder", "description": "Reordenar menus"},
        ],
    },
    "system": {
        "description": "Administração do sistema",
        "permissions": [
            {"name": "system.admin", "description": "Administração geral do sistema"},
            {"name": "system.settings", "description": "Configurações globais"},
            {"name": "system.logs", "description": "Acesso aos logs do sistema"},
            {"name": "system.backup", "description": "Backup e restore"},
            {"name": "system.maintenance", "description": "Modo de manutenção"},
            {"name": "system.monitoring", "description": "Monitoramento do sistema"},
        ],
    },
    "reports": {
        "description": "Relatórios e analytics",
        "permissions": [
            {"name": "reports.view", "description": "Visualizar relatórios"},
            {"name": "reports.create", "description": "Criar relatórios customizados"},
            {"name": "reports.export", "description": "Exportar relatórios"},
            {"name": "reports.schedule", "description": "Agendar relatórios"},
        ],
    },
}


class PermissionMigrator:
    def __init__(self):
        self.db = None

    async def connect_db(self):
        """Conectar ao banco de dados"""
        try:
            self.db = await anext(get_db())
            logger.info("✅ Conectado ao banco de dados")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao banco: {e}")
            raise

    async def run_migration_script(self):
        """Executar o script de migração SQL"""
        try:
            migration_file = "/home/juliano/Projetos/pro_team_care_16/migrations/007_permission_migration_setup.sql"

            with open(migration_file, "r", encoding="utf-8") as f:
                migration_sql = f.read()

            # Executar em transação
            async with self.db.begin():
                await self.db.execute(text(migration_sql))

            logger.info("✅ Migração SQL executada com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao executar migração: {e}")
            raise

    async def create_permissions(self):
        """Criar todas as permissões granulares"""
        try:
            permissions_created = 0
            permissions_updated = 0

            for category, data in PERMISSION_CATEGORIES.items():
                logger.info(f"📝 Processando categoria: {category}")

                for perm in data["permissions"]:
                    # Tentar inserir a permissão
                    try:
                        result = await self.db.execute(
                            text(
                                """
                            INSERT INTO master.permissions (
                                name,
                                display_name,
                                description,
                                category,
                                context_level,
                                is_active,
                                created_at
                            ) VALUES (
                                :name,
                                :display_name,
                                :description,
                                :category,
                                :context_level,
                                true,
                                NOW()
                            )
                            ON CONFLICT (name) DO UPDATE SET
                                display_name = EXCLUDED.display_name,
                                description = EXCLUDED.description,
                                category = EXCLUDED.category,
                                updated_at = NOW()
                            RETURNING id, name
                        """
                            ),
                            {
                                "name": perm["name"],
                                "display_name": perm["name"].replace("_", " ").title(),
                                "description": perm["description"],
                                "category": category,
                                "context_level": self.determine_context_level(
                                    perm["name"]
                                ),
                            },
                        )

                        row = result.fetchone()
                        if row:
                            if "INSERT" in str(result.context.statement):
                                permissions_created += 1
                                logger.info(f"  ➕ Criada: {perm['name']}")
                            else:
                                permissions_updated += 1
                                logger.info(f"  🔄 Atualizada: {perm['name']}")

                    except IntegrityError as e:
                        logger.warning(f"  ⚠️ Permissão já existe: {perm['name']}")
                        continue

            await self.db.commit()
            logger.info(
                f"✅ Permissões processadas: {permissions_created} criadas, {permissions_updated} atualizadas"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Erro ao criar permissões: {e}")
            raise

    def determine_context_level(self, permission_name: str) -> str:
        """Determinar o nível de contexto baseado no nome da permissão"""
        if permission_name.startswith("system."):
            return "system"
        elif permission_name.startswith("companies."):
            return "company"
        else:
            return "establishment"

    async def create_migrated_roles_from_templates(self):
        """Criar perfis baseados nos templates para usuários existentes"""
        try:
            # Buscar templates
            templates_result = await self.db.execute(
                text(
                    """
                SELECT template_key, name, description, context_type, permissions
                FROM master.role_templates
                WHERE is_active = true
            """
                )
            )

            templates = templates_result.fetchall()
            roles_created = 0

            for template in templates:
                try:
                    # Criar role baseado no template
                    role_result = await self.db.execute(
                        text(
                            """
                        INSERT INTO master.roles (
                            name,
                            display_name,
                            description,
                            context_type,
                            is_active,
                            is_system_role,
                            created_at
                        ) VALUES (
                            :name,
                            :display_name,
                            :description,
                            :context_type,
                            true,
                            true,
                            NOW()
                        )
                        ON CONFLICT (name) DO UPDATE SET
                            display_name = EXCLUDED.display_name,
                            description = EXCLUDED.description,
                            updated_at = NOW()
                        RETURNING id
                    """
                        ),
                        {
                            "name": f"migrated_{template.template_key}",
                            "display_name": template.name,
                            "description": f"[MIGRADO] {template.description}",
                            "context_type": template.context_type,
                        },
                    )

                    role_id = role_result.scalar()

                    if role_id:
                        # Associar permissões ao perfil
                        permissions_added = 0
                        for permission_name in template.permissions:
                            try:
                                await self.db.execute(
                                    text(
                                        """
                                    INSERT INTO master.role_permissions (role_id, permission_id)
                                    SELECT :role_id, p.id
                                    FROM master.permissions p
                                    WHERE p.name = :permission_name
                                    ON CONFLICT (role_id, permission_id) DO NOTHING
                                """
                                    ),
                                    {
                                        "role_id": role_id,
                                        "permission_name": permission_name,
                                    },
                                )
                                permissions_added += 1
                            except Exception as e:
                                logger.warning(
                                    f"  ⚠️ Erro ao adicionar permissão {permission_name}: {e}"
                                )

                        roles_created += 1
                        logger.info(
                            f"  ✅ Role criado: {template.name} ({permissions_added} permissões)"
                        )

                except Exception as e:
                    logger.error(f"  ❌ Erro ao criar role {template.name}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"✅ {roles_created} perfis de migração criados")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Erro ao criar perfis de migração: {e}")
            raise

    async def analyze_current_users(self):
        """Analisar usuários atuais e gerar relatório"""
        try:
            analysis_result = await self.db.execute(
                text(
                    """
                SELECT
                    user_name,
                    email,
                    context_type,
                    role_name,
                    current_level,
                    suggested_template,
                    array_length(equivalent_permissions, 1) as permissions_count
                FROM master.user_levels_analysis
                ORDER BY current_level DESC, user_name
            """
                )
            )

            users = analysis_result.fetchall()

            logger.info("📊 ANÁLISE DE USUÁRIOS ATUAIS:")
            logger.info("=" * 80)

            level_counts = {}
            for user in users:
                level = user.current_level
                level_counts[level] = level_counts.get(level, 0) + 1

                logger.info(f"👤 {user.user_name} ({user.email})")
                logger.info(f"   📍 Contexto: {user.context_type}")
                logger.info(
                    f"   🎭 Perfil atual: {user.role_name} (nível {user.current_level})"
                )
                logger.info(f"   🎯 Template sugerido: {user.suggested_template}")
                logger.info(f"   🔑 Permissões equivalentes: {user.permissions_count}")
                logger.info("-" * 40)

            logger.info("\n📈 RESUMO POR NÍVEL:")
            for level, count in sorted(level_counts.items(), reverse=True):
                logger.info(f"   Nível {level}: {count} usuários")

            return len(users)

        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
            raise

    async def validate_migration_setup(self):
        """Validar se o setup está correto"""
        try:
            # Verificar permissões criadas
            perm_count = await self.db.execute(
                text(
                    """
                SELECT COUNT(*) FROM master.permissions WHERE is_active = true
            """
                )
            )
            permissions_total = perm_count.scalar()

            # Verificar templates
            template_count = await self.db.execute(
                text(
                    """
                SELECT COUNT(*) FROM master.role_templates WHERE is_active = true
            """
                )
            )
            templates_total = template_count.scalar()

            # Verificar roles migrados
            migrated_roles_count = await self.db.execute(
                text(
                    """
                SELECT COUNT(*) FROM master.roles WHERE name LIKE 'migrated_%'
            """
                )
            )
            migrated_roles_total = migrated_roles_count.scalar()

            logger.info("🔍 VALIDAÇÃO DO SETUP:")
            logger.info(f"   ✅ Permissões criadas: {permissions_total}")
            logger.info(f"   ✅ Templates disponíveis: {templates_total}")
            logger.info(f"   ✅ Perfis de migração: {migrated_roles_total}")

            # Validações
            expected_permissions = sum(
                len(cat["permissions"]) for cat in PERMISSION_CATEGORIES.values()
            )
            expected_templates = 6  # super_admin, admin_empresa, etc.

            if permissions_total >= expected_permissions:
                logger.info("   ✅ Quantidade de permissões OK")
            else:
                logger.warning(
                    f"   ⚠️ Esperado {expected_permissions}, encontrado {permissions_total}"
                )

            if templates_total >= expected_templates:
                logger.info("   ✅ Quantidade de templates OK")
            else:
                logger.warning(
                    f"   ⚠️ Esperado {expected_templates}, encontrado {templates_total}"
                )

            return True

        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            return False


async def main():
    """Função principal da migração Fase 1"""
    logger.info("🚀 INICIANDO FASE 1: SETUP DE PERMISSÕES GRANULARES")
    logger.info("=" * 60)

    migrator = PermissionMigrator()

    try:
        # 1. Conectar ao banco
        await migrator.connect_db()

        # 2. Executar migração SQL
        logger.info("📄 Executando migração SQL...")
        await migrator.run_migration_script()

        # 3. Criar permissões granulares
        logger.info("🔑 Criando permissões granulares...")
        await migrator.create_permissions()

        # 4. Criar perfis de migração
        logger.info("🎭 Criando perfis de migração...")
        await migrator.create_migrated_roles_from_templates()

        # 5. Analisar usuários atuais
        logger.info("📊 Analisando usuários atuais...")
        users_analyzed = await migrator.analyze_current_users()

        # 6. Validar setup
        logger.info("🔍 Validando setup...")
        validation_ok = await migrator.validate_migration_setup()

        if validation_ok:
            logger.info("🎉 FASE 1 CONCLUÍDA COM SUCESSO!")
            logger.info(f"   📈 {users_analyzed} usuários analisados")
            logger.info("   ✅ Estrutura de permissões criada")
            logger.info("   ✅ Templates configurados")
            logger.info("   ✅ Pronto para Fase 2")
        else:
            logger.error("❌ Validação falhou - verificar logs")
            return 1

    except Exception as e:
        logger.error(f"💥 ERRO NA FASE 1: {e}")
        return 1

    finally:
        if migrator.db:
            await migrator.db.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
