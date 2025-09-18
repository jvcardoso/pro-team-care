#!/usr/bin/env python3
"""
Script simplificado para executar migração Fase 1
Executa comandos SQL individuais para evitar problemas de múltiplos comandos
"""

import asyncio
import logging
import sys
from typing import List

from sqlalchemy import text

# Adicionar o caminho da aplicação
sys.path.append("/home/juliano/Projetos/pro_team_care_16")

from app.infrastructure.database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Comandos SQL divididos individualmente
SQL_COMMANDS = [
    # 1. Criar tabela de mapeamento
    """
    CREATE TABLE IF NOT EXISTS master.level_permission_mapping (
        id BIGSERIAL PRIMARY KEY,
        level_min INTEGER NOT NULL,
        level_max INTEGER NOT NULL,
        permission_name VARCHAR(100) NOT NULL,
        context_type VARCHAR(50) NOT NULL DEFAULT 'establishment',
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """,
    # 2. Índices para performance
    "CREATE INDEX IF NOT EXISTS level_permission_mapping_level_idx ON master.level_permission_mapping(level_min, level_max)",
    "CREATE INDEX IF NOT EXISTS level_permission_mapping_permission_idx ON master.level_permission_mapping(permission_name)",
    # 3. Limpar dados existentes
    "DELETE FROM master.level_permission_mapping",
    # 4. Popular mapeamento - Sistema (90-100)
    """
    INSERT INTO master.level_permission_mapping (level_min, level_max, permission_name, context_type, description) VALUES
    (90, 100, 'system.admin', 'system', 'Administração completa do sistema'),
    (90, 100, 'system.settings', 'system', 'Configurações globais do sistema'),
    (90, 100, 'system.logs', 'system', 'Acesso aos logs do sistema'),
    (90, 100, 'system.backup', 'system', 'Backup e restore do sistema')
    """,
    # 5. Popular mapeamento - Admin Empresa (80-100)
    """
    INSERT INTO master.level_permission_mapping (level_min, level_max, permission_name, context_type, description) VALUES
    (80, 100, 'companies.create', 'company', 'Criar empresas'),
    (80, 100, 'companies.delete', 'company', 'Excluir empresas'),
    (80, 100, 'companies.settings', 'company', 'Configurações da empresa'),
    (80, 100, 'users.create', 'establishment', 'Criar usuários'),
    (80, 100, 'users.delete', 'establishment', 'Excluir usuários'),
    (80, 100, 'users.permissions', 'establishment', 'Gerenciar permissões de usuários'),
    (80, 100, 'establishments.create', 'company', 'Criar estabelecimentos'),
    (80, 100, 'establishments.delete', 'establishment', 'Excluir estabelecimentos')
    """,
    # 6. Popular mapeamento - Admin Estabelecimento (60-100)
    """
    INSERT INTO master.level_permission_mapping (level_min, level_max, permission_name, context_type, description) VALUES
    (60, 100, 'companies.edit', 'company', 'Editar empresas'),
    (60, 100, 'companies.view', 'company', 'Visualizar empresas'),
    (60, 100, 'establishments.edit', 'establishment', 'Editar estabelecimentos'),
    (60, 100, 'establishments.settings', 'establishment', 'Configurações do estabelecimento'),
    (60, 100, 'users.edit', 'establishment', 'Editar usuários'),
    (60, 100, 'users.list', 'establishment', 'Listar usuários'),
    (60, 100, 'roles.assign', 'establishment', 'Atribuir perfis')
    """,
    # 7. Popular mapeamento - Operacional (40-100)
    """
    INSERT INTO master.level_permission_mapping (level_min, level_max, permission_name, context_type, description) VALUES
    (40, 100, 'users.view', 'establishment', 'Visualizar usuários'),
    (40, 100, 'establishments.view', 'establishment', 'Visualizar estabelecimentos'),
    (40, 100, 'companies.list', 'company', 'Listar empresas')
    """,
    # 8. Popular mapeamento - Perfis
    """
    INSERT INTO master.level_permission_mapping (level_min, level_max, permission_name, context_type, description) VALUES
    (70, 100, 'roles.create', 'establishment', 'Criar perfis'),
    (70, 100, 'roles.edit', 'establishment', 'Editar perfis'),
    (70, 100, 'roles.delete', 'establishment', 'Excluir perfis'),
    (40, 100, 'roles.view', 'establishment', 'Visualizar perfis'),
    (40, 100, 'roles.list', 'establishment', 'Listar perfis')
    """,
    # 9. Criar tabela de templates
    """
    CREATE TABLE IF NOT EXISTS master.role_templates (
        id BIGSERIAL PRIMARY KEY,
        template_key VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(125) NOT NULL,
        description TEXT,
        equivalent_level_min INTEGER,
        equivalent_level_max INTEGER,
        context_type VARCHAR(50) NOT NULL DEFAULT 'establishment',
        permissions TEXT[],
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    # 10. Índices para templates
    "CREATE INDEX IF NOT EXISTS role_templates_key_idx ON master.role_templates(template_key)",
    "CREATE INDEX IF NOT EXISTS role_templates_level_idx ON master.role_templates(equivalent_level_min, equivalent_level_max)",
    # 11. Limpar templates existentes
    "DELETE FROM master.role_templates",
    # 12. Inserir template super_admin
    """
    INSERT INTO master.role_templates (template_key, name, description, equivalent_level_min, equivalent_level_max, context_type, permissions) VALUES
    ('super_admin', 'Super Administrador', 'Acesso total ao sistema', 90, 100, 'system',
     ARRAY['system.admin', 'system.settings', 'system.logs', 'system.backup',
           'companies.create', 'companies.edit', 'companies.delete', 'companies.settings',
           'users.create', 'users.edit', 'users.delete', 'users.permissions',
           'roles.create', 'roles.edit', 'roles.delete', 'roles.assign'])
    """,
    # 13. Inserir template admin_empresa
    """
    INSERT INTO master.role_templates (template_key, name, description, equivalent_level_min, equivalent_level_max, context_type, permissions) VALUES
    ('admin_empresa', 'Administrador da Empresa', 'Gestão completa da empresa', 80, 89, 'company',
     ARRAY['companies.edit', 'companies.settings', 'companies.view',
           'establishments.create', 'establishments.edit', 'establishments.delete',
           'users.create', 'users.edit', 'users.delete', 'users.list', 'users.view',
           'roles.create', 'roles.edit', 'roles.assign'])
    """,
    # 14. Inserir outros templates
    """
    INSERT INTO master.role_templates (template_key, name, description, equivalent_level_min, equivalent_level_max, context_type, permissions) VALUES
    ('admin_estabelecimento', 'Administrador do Estabelecimento', 'Gestão do estabelecimento', 60, 79, 'establishment',
     ARRAY['establishments.edit', 'establishments.settings', 'establishments.view',
           'users.edit', 'users.list', 'users.view',
           'companies.view', 'companies.list',
           'roles.view', 'roles.assign']),
    ('gerente_operacional', 'Gerente Operacional', 'Operações diárias', 50, 69, 'establishment',
     ARRAY['users.view', 'users.list',
           'establishments.view',
           'companies.view', 'companies.list',
           'roles.view']),
    ('operador', 'Operador', 'Acesso básico para operações', 40, 59, 'establishment',
     ARRAY['users.view', 'establishments.view', 'companies.view'])
    """,
]


async def execute_migration():
    """Executar comandos da migração"""
    logger.info("🚀 Iniciando migração Fase 1...")

    try:
        async for db in get_db():
            total_commands = len(SQL_COMMANDS)

            for i, sql_command in enumerate(SQL_COMMANDS, 1):
                try:
                    logger.info(f"📝 Executando comando {i}/{total_commands}...")
                    await db.execute(text(sql_command.strip()))
                    await db.commit()
                    logger.info(f"✅ Comando {i} executado com sucesso")

                except Exception as e:
                    logger.error(f"❌ Erro no comando {i}: {e}")
                    await db.rollback()
                    # Continuar com os próximos comandos
                    continue

            logger.info("🎉 Migração SQL concluída!")

            # Verificar resultados
            result = await db.execute(
                text("SELECT COUNT(*) FROM master.level_permission_mapping")
            )
            mapping_count = result.scalar()

            result = await db.execute(
                text("SELECT COUNT(*) FROM master.role_templates")
            )
            template_count = result.scalar()

            logger.info(f"📊 Resultados:")
            logger.info(f"   🗂️ Mapeamentos criados: {mapping_count}")
            logger.info(f"   📋 Templates criados: {template_count}")

            return True

    except Exception as e:
        logger.error(f"💥 Erro na migração: {e}")
        return False


async def main():
    """Função principal"""
    logger.info("=" * 60)
    logger.info("🚀 FASE 1: SETUP DE PERMISSÕES GRANULARES")
    logger.info("=" * 60)

    success = await execute_migration()

    if success:
        logger.info("✅ FASE 1 CONCLUÍDA COM SUCESSO!")
        logger.info("📋 Próximos passos:")
        logger.info("   1. Verificar dados criados")
        logger.info("   2. Testar sistema de cache")
        logger.info("   3. Iniciar Fase 2 (migração de endpoints)")
        return 0
    else:
        logger.error("❌ FASE 1 FALHOU - verificar logs")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
