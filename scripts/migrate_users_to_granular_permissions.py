#!/usr/bin/env python3
"""
Script de Migração de Usuários - Fase 3
Migra usuários existentes do sistema de níveis para permissões granulares
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional

from sqlalchemy import text

# Adicionar o caminho da aplicação
sys.path.append("/home/juliano/Projetos/pro_team_care_16")

from app.infrastructure.database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserMigrator:
    """Migrador de usuários para sistema de permissões granulares"""

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

    async def analyze_current_users(self) -> Dict[str, Any]:
        """Analisar usuários atuais e seus níveis"""
        logger.info("📊 Analisando usuários atuais...")

        try:
            # Buscar usuários com seus roles e níveis
            result = await self.db.execute(
                text(
                    """
                SELECT
                    u.id as user_id,
                    u.email_address,
                    u.is_system_admin,
                    u.company_id,
                    u.establishment_id,
                    ur.context_type as ur_context_type,
                    ur.context_id,
                    r.name as role_name,
                    r.level as role_level,
                    r.context_type as role_context,
                    ur.status as user_role_status
                FROM master.users u
                LEFT JOIN master.user_roles ur ON u.id = ur.user_id
                    AND ur.status = 'active'
                    AND ur.deleted_at IS NULL
                LEFT JOIN master.roles r ON ur.role_id = r.id
                WHERE u.deleted_at IS NULL
                ORDER BY u.id, r.level DESC
            """
                )
            )

            users_data = {}
            for row in result.fetchall():
                user_id = row.user_id
                if user_id not in users_data:
                    users_data[user_id] = {
                        "email": row.email_address,
                        "is_system_admin": row.is_system_admin,
                        "company_id": row.company_id,
                        "establishment_id": row.establishment_id,
                        "roles": [],
                    }

                if row.role_name:  # Se o usuário tem role
                    users_data[user_id]["roles"].append(
                        {
                            "name": row.role_name,
                            "level": row.role_level,
                            "context_type": row.role_context,
                            "ur_context_type": row.ur_context_type,
                            "context_id": row.context_id,
                            "status": row.user_role_status,
                        }
                    )

            logger.info(f"📈 Encontrados {len(users_data)} usuários para análise")

            # Estatísticas por nível
            level_stats = {}
            users_without_roles = 0

            for user_id, user_data in users_data.items():
                if not user_data["roles"]:
                    users_without_roles += 1
                else:
                    # Pegar o nível máximo do usuário
                    max_level = max(role["level"] for role in user_data["roles"])
                    level_stats[max_level] = level_stats.get(max_level, 0) + 1

            logger.info(f"📊 Estatísticas:")
            logger.info(f"   👥 Usuários sem roles: {users_without_roles}")
            for level, count in sorted(level_stats.items(), reverse=True):
                logger.info(f"   🎚️ Nível {level}: {count} usuários")

            return {
                "users": users_data,
                "stats": level_stats,
                "users_without_roles": users_without_roles,
            }

        except Exception as e:
            logger.error(f"❌ Erro na análise: {e}")
            raise

    async def get_role_templates(self) -> Dict[str, Any]:
        """Buscar templates de roles disponíveis"""
        logger.info("📋 Buscando templates de roles...")

        try:
            result = await self.db.execute(
                text(
                    """
                SELECT
                    template_key,
                    name,
                    description,
                    equivalent_level_min,
                    equivalent_level_max,
                    context_type,
                    permissions,
                    is_active
                FROM master.role_templates
                WHERE is_active = true
                ORDER BY equivalent_level_min DESC
            """
                )
            )

            templates = {}
            for row in result.fetchall():
                templates[row.template_key] = {
                    "name": row.name,
                    "description": row.description,
                    "level_min": row.equivalent_level_min,
                    "level_max": row.equivalent_level_max,
                    "context_type": row.context_type,
                    "permissions": row.permissions or [],
                    "is_active": row.is_active,
                }

            logger.info(f"📋 Encontrados {len(templates)} templates ativos")
            for key, template in templates.items():
                logger.info(
                    f"   🎯 {key}: {template['name']} (níveis {template['level_min']}-{template['level_max']})"
                )

            return templates

        except Exception as e:
            logger.error(f"❌ Erro ao buscar templates: {e}")
            raise

    def suggest_template_for_level(
        self, level: int, templates: Dict[str, Any]
    ) -> Optional[str]:
        """Sugerir template baseado no nível do usuário"""
        best_template = None

        for template_key, template in templates.items():
            level_min = template["level_min"]
            level_max = template["level_max"]

            if level_min <= level <= level_max:
                # Se encontrar uma correspondência exata, usar ela
                if (
                    not best_template
                    or template["level_min"] > templates[best_template]["level_min"]
                ):
                    best_template = template_key

        return best_template

    async def create_granular_roles_from_templates(
        self, templates: Dict[str, Any]
    ) -> Dict[str, int]:
        """Criar roles granulares baseados nos templates"""
        logger.info("🎭 Criando roles granulares a partir dos templates...")

        created_roles = {}

        try:
            for template_key, template in templates.items():
                # Criar role granular
                role_name = f"granular_{template_key}"

                # Verificar se já existe
                check_result = await self.db.execute(
                    text(
                        """
                    SELECT id FROM master.roles WHERE name = :role_name
                """
                    ),
                    {"role_name": role_name},
                )

                existing_role = check_result.fetchone()
                if existing_role:
                    created_roles[template_key] = existing_role.id
                    logger.info(
                        f"   ♻️ Role já existe: {role_name} (ID: {existing_role.id})"
                    )
                    continue

                # Criar novo role
                role_result = await self.db.execute(
                    text(
                        """
                    INSERT INTO master.roles (
                        name, display_name, description, level, context_type,
                        is_active, is_system_role, created_at, updated_at
                    ) VALUES (
                        :name, :display_name, :description, :level, :context_type,
                        true, false, NOW(), NOW()
                    ) RETURNING id
                """
                    ),
                    {
                        "name": role_name,
                        "display_name": f"[GRANULAR] {template['name']}",
                        "description": f"Role migrado automaticamente: {template['description']}",
                        "level": template[
                            "level_max"
                        ],  # Usar nível máximo como referência
                        "context_type": template["context_type"],
                    },
                )

                role_id = role_result.scalar()
                created_roles[template_key] = role_id

                # Associar permissões ao role
                permissions_added = 0
                for permission_name in template["permissions"]:
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
                            {"role_id": role_id, "permission_name": permission_name},
                        )
                        permissions_added += 1
                    except Exception as e:
                        logger.warning(
                            f"     ⚠️ Erro ao associar permissão {permission_name}: {e}"
                        )

                logger.info(
                    f"   ✅ Criado: {role_name} (ID: {role_id}, {permissions_added} permissões)"
                )

            await self.db.commit()
            logger.info(f"🎭 {len(created_roles)} roles granulares prontos")
            return created_roles

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Erro ao criar roles: {e}")
            raise

    async def migrate_users_to_granular_permissions(
        self,
        users_data: Dict[str, Any],
        templates: Dict[str, Any],
        granular_roles: Dict[str, int],
    ) -> Dict[str, Any]:
        """Migrar usuários para sistema granular"""
        logger.info("🚀 Iniciando migração de usuários...")

        migration_stats = {"migrated": 0, "skipped": 0, "errors": 0, "details": []}

        try:
            for user_id, user_data in users_data.items():
                try:
                    # Skip usuários sem roles
                    if not user_data["roles"]:
                        migration_stats["skipped"] += 1
                        logger.info(
                            f"   ⏭️ Usuário {user_data['email']}: sem roles para migrar"
                        )
                        continue

                    # Determinar o nível máximo do usuário
                    max_level = max(role["level"] for role in user_data["roles"])

                    # Sugerir template
                    suggested_template = self.suggest_template_for_level(
                        max_level, templates
                    )

                    if not suggested_template:
                        migration_stats["skipped"] += 1
                        logger.warning(
                            f"   ⚠️ Usuário {user_data['email']}: nenhum template encontrado para nível {max_level}"
                        )
                        continue

                    # Verificar se já foi migrado
                    check_result = await self.db.execute(
                        text(
                            """
                        SELECT ur.id FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = :user_id
                        AND r.name LIKE 'granular_%'
                        AND ur.status = 'active'
                        AND ur.deleted_at IS NULL
                    """
                        ),
                        {"user_id": user_id},
                    )

                    if check_result.fetchone():
                        migration_stats["skipped"] += 1
                        logger.info(f"   ♻️ Usuário {user_data['email']}: já migrado")
                        continue

                    # Atribuir role granular
                    granular_role_id = granular_roles[suggested_template]

                    # Determinar contexto para o role granular
                    # Primeiro verificar se o usuário tem establishment_id
                    establishment_id = user_data.get("establishment_id")

                    if establishment_id:
                        context_type = "establishment"
                        context_id = establishment_id
                    else:
                        # Se não tem establishment, usar contexto company
                        context_type = "company"
                        context_id = user_data["company_id"]

                    # Criar user_role granular
                    await self.db.execute(
                        text(
                            """
                        INSERT INTO master.user_roles (
                            user_id, role_id, context_type, context_id,
                            status, created_at, updated_at
                        ) VALUES (
                            :user_id, :role_id, :context_type, :context_id,
                            'active', NOW(), NOW()
                        )
                    """
                        ),
                        {
                            "user_id": user_id,
                            "role_id": granular_role_id,
                            "context_type": context_type,
                            "context_id": context_id,
                        },
                    )

                    migration_stats["migrated"] += 1
                    migration_stats["details"].append(
                        {
                            "user_id": user_id,
                            "email": user_data["email"],
                            "original_level": max_level,
                            "template": suggested_template,
                            "context": f"{context_type}:{context_id}",
                        }
                    )

                    logger.info(
                        f"   ✅ Migrado: {user_data['email']} → {suggested_template} (nível {max_level})"
                    )

                except Exception as e:
                    migration_stats["errors"] += 1
                    logger.error(f"   ❌ Erro ao migrar {user_data['email']}: {e}")

            await self.db.commit()

            logger.info(f"📊 Resultado da migração:")
            logger.info(f"   ✅ Migrados: {migration_stats['migrated']}")
            logger.info(f"   ⏭️ Ignorados: {migration_stats['skipped']}")
            logger.info(f"   ❌ Erros: {migration_stats['errors']}")

            return migration_stats

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Erro na migração: {e}")
            raise

    async def validate_migration(self) -> Dict[str, Any]:
        """Validar resultado da migração"""
        logger.info("🔍 Validando migração...")

        try:
            # Contar usuários com permissões granulares
            result = await self.db.execute(
                text(
                    """
                SELECT COUNT(DISTINCT ur.user_id) as users_with_granular
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                WHERE r.name LIKE 'granular_%'
                AND ur.status = 'active'
                AND ur.deleted_at IS NULL
            """
                )
            )
            users_with_granular = result.scalar()

            # Contar total de usuários ativos
            result = await self.db.execute(
                text(
                    """
                SELECT COUNT(*) as total_users
                FROM master.users
                WHERE deleted_at IS NULL
            """
                )
            )
            total_users = result.scalar()

            # Contar usuários com permissões específicas
            result = await self.db.execute(
                text(
                    """
                SELECT
                    p.name as permission_name,
                    COUNT(DISTINCT ur.user_id) as user_count
                FROM master.user_roles ur
                JOIN master.roles r ON ur.role_id = r.id
                JOIN master.role_permissions rp ON r.id = rp.role_id
                JOIN master.permissions p ON rp.permission_id = p.id
                WHERE r.name LIKE 'granular_%'
                AND ur.status = 'active'
                AND ur.deleted_at IS NULL
                GROUP BY p.name
                ORDER BY user_count DESC
                LIMIT 10
            """
                )
            )

            permission_usage = []
            for row in result.fetchall():
                permission_usage.append(
                    {"permission": row.permission_name, "users": row.user_count}
                )

            validation_result = {
                "users_with_granular": users_with_granular,
                "total_users": total_users,
                "migration_coverage": (
                    (users_with_granular / total_users * 100) if total_users > 0 else 0
                ),
                "permission_usage": permission_usage,
            }

            logger.info(f"📈 Validação:")
            logger.info(f"   👥 Usuários totais: {total_users}")
            logger.info(f"   🎯 Usuários migrados: {users_with_granular}")
            logger.info(
                f"   📊 Cobertura: {validation_result['migration_coverage']:.1f}%"
            )

            logger.info(f"🔑 Permissões mais usadas:")
            for perm in permission_usage[:5]:
                logger.info(f"   • {perm['permission']}: {perm['users']} usuários")

            return validation_result

        except Exception as e:
            logger.error(f"❌ Erro na validação: {e}")
            raise


async def main():
    """Função principal da migração"""
    logger.info("=" * 60)
    logger.info("🚀 MIGRAÇÃO USUÁRIOS - FASE 3")
    logger.info("=" * 60)

    migrator = UserMigrator()

    try:
        # 1. Conectar ao banco
        await migrator.connect_db()

        # 2. Analisar usuários atuais
        users_analysis = await migrator.analyze_current_users()

        # 3. Buscar templates disponíveis
        templates = await migrator.get_role_templates()

        # 4. Criar roles granulares
        granular_roles = await migrator.create_granular_roles_from_templates(templates)

        # 5. Migrar usuários
        migration_result = await migrator.migrate_users_to_granular_permissions(
            users_analysis["users"], templates, granular_roles
        )

        # 6. Validar migração
        validation = await migrator.validate_migration()

        # Resultado final
        logger.info("\n" + "=" * 60)
        logger.info("🎉 MIGRAÇÃO CONCLUÍDA!")
        logger.info("=" * 60)
        logger.info(f"✅ Usuários migrados: {migration_result['migrated']}")
        logger.info(f"⏭️ Usuários ignorados: {migration_result['skipped']}")
        logger.info(f"❌ Erros: {migration_result['errors']}")
        logger.info(f"📊 Cobertura total: {validation['migration_coverage']:.1f}%")

        if validation["migration_coverage"] >= 80:
            logger.info(
                "🚀 Migração bem-sucedida! Sistema pronto para usar permissões granulares."
            )
            return 0
        else:
            logger.warning(
                "⚠️ Migração parcial. Alguns usuários podem precisar de ajustes manuais."
            )
            return 0  # Ainda considera sucesso, mas com avisos

    except Exception as e:
        logger.error(f"💥 ERRO NA MIGRAÇÃO: {e}")
        return 1

    finally:
        if migrator.db:
            await migrator.db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
