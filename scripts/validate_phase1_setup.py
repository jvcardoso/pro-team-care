#!/usr/bin/env python3
"""
Script de Validação - Fase 1
Verifica se o setup de permissões granulares foi executado corretamente
"""

import asyncio
import logging
import sys
from typing import Any, Dict

from sqlalchemy import text

# Adicionar o caminho da aplicação
sys.path.append("/home/juliano/Projetos/pro_team_care_16")

from app.infrastructure.database import get_db

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Phase1Validator:
    """Validador para Fase 1 da migração"""

    async def validate_database_setup(self) -> Dict[str, Any]:
        """Validar estrutura do banco de dados"""
        logger.info("🔍 Validando estrutura do banco...")

        validation_results = {
            "tables": {},
            "indexes": {},
            "data": {},
            "functions": {},
            "views": {},
        }

        try:
            async for db in get_db():
                # 1. Verificar tabelas criadas
                tables_to_check = ["level_permission_mapping", "role_templates"]

                for table in tables_to_check:
                    result = await db.execute(
                        text(
                            f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_schema = 'master'
                            AND table_name = '{table}'
                        )
                    """
                        )
                    )
                    exists = result.scalar()
                    validation_results["tables"][table] = exists

                    if exists:
                        # Contar registros
                        count_result = await db.execute(
                            text(f"SELECT COUNT(*) FROM master.{table}")
                        )
                        count = count_result.scalar()
                        validation_results["data"][table] = count
                        logger.info(f"  ✅ Tabela {table}: {count} registros")
                    else:
                        logger.error(f"  ❌ Tabela {table} não encontrada")

                # 2. Verificar índices
                indexes_to_check = [
                    "level_permission_mapping_level_idx",
                    "level_permission_mapping_permission_idx",
                    "role_templates_key_idx",
                    "role_templates_level_idx",
                ]

                for index in indexes_to_check:
                    result = await db.execute(
                        text(
                            f"""
                        SELECT EXISTS (
                            SELECT 1 FROM pg_indexes
                            WHERE schemaname = 'master'
                            AND indexname = '{index}'
                        )
                    """
                        )
                    )
                    exists = result.scalar()
                    validation_results["indexes"][index] = exists
                    status = "✅" if exists else "❌"
                    logger.info(f"  {status} Índice {index}")

                return validation_results

        except Exception as e:
            logger.error(f"❌ Erro na validação do banco: {e}")
            raise

    async def analyze_permission_mappings(self) -> Dict[str, Any]:
        """Analisar mapeamentos de permissões criados"""
        logger.info("📊 Analisando mapeamentos de permissões...")

        try:
            async for db in get_db():
                # Análise por contexto
                result = await db.execute(
                    text(
                        """
                    SELECT
                        context_type,
                        COUNT(*) as permission_count,
                        MIN(level_min) as min_level,
                        MAX(level_max) as max_level
                    FROM master.level_permission_mapping
                    GROUP BY context_type
                    ORDER BY context_type
                """
                    )
                )

                context_analysis = {}
                for row in result.fetchall():
                    context_analysis[row.context_type] = {
                        "permission_count": row.permission_count,
                        "level_range": f"{row.min_level}-{row.max_level}",
                    }
                    logger.info(
                        f"  📋 {row.context_type}: {row.permission_count} permissões (níveis {row.min_level}-{row.max_level})"
                    )

                # Análise por nível
                result = await db.execute(
                    text(
                        """
                    SELECT
                        level_min,
                        level_max,
                        COUNT(*) as permission_count,
                        array_agg(permission_name ORDER BY permission_name) as permissions
                    FROM master.level_permission_mapping
                    GROUP BY level_min, level_max
                    ORDER BY level_min DESC
                """
                    )
                )

                level_analysis = {}
                for row in result.fetchall():
                    level_key = f"{row.level_min}-{row.level_max}"
                    level_analysis[level_key] = {
                        "permission_count": row.permission_count,
                        "permissions": row.permissions,
                    }
                    logger.info(
                        f"  🎚️ Nível {level_key}: {row.permission_count} permissões"
                    )

                return {"by_context": context_analysis, "by_level": level_analysis}

        except Exception as e:
            logger.error(f"❌ Erro na análise de mapeamentos: {e}")
            raise

    async def analyze_role_templates(self) -> Dict[str, Any]:
        """Analisar templates de perfis criados"""
        logger.info("🎭 Analisando templates de perfis...")

        try:
            async for db in get_db():
                result = await db.execute(
                    text(
                        """
                    SELECT
                        template_key,
                        name,
                        context_type,
                        equivalent_level_min,
                        equivalent_level_max,
                        array_length(permissions, 1) as permission_count,
                        permissions
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
                        "context_type": row.context_type,
                        "level_range": f"{row.equivalent_level_min}-{row.equivalent_level_max}",
                        "permission_count": row.permission_count or 0,
                        "permissions": row.permissions or [],
                    }

                    logger.info(f"  🎯 {row.template_key}: {row.name}")
                    logger.info(f"      📍 Contexto: {row.context_type}")
                    logger.info(
                        f"      🎚️ Nível: {row.equivalent_level_min}-{row.equivalent_level_max}"
                    )
                    logger.info(f"      🔑 Permissões: {row.permission_count or 0}")

                return templates

        except Exception as e:
            logger.error(f"❌ Erro na análise de templates: {e}")
            raise

    async def test_permission_functions(self) -> Dict[str, Any]:
        """Testar funções de permissão (se criadas)"""
        logger.info("🧪 Testando funções de permissão...")

        test_results = {}

        try:
            async for db in get_db():
                # Verificar se as funções existem
                functions_to_check = [
                    "get_permissions_for_level",
                    "suggest_role_template_for_level",
                ]

                for func_name in functions_to_check:
                    result = await db.execute(
                        text(
                            f"""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.routines
                            WHERE routine_schema = 'master'
                            AND routine_name = '{func_name}'
                        )
                    """
                        )
                    )
                    exists = result.scalar()
                    test_results[func_name] = {"exists": exists}

                    if exists:
                        try:
                            # Testar função get_permissions_for_level
                            if func_name == "get_permissions_for_level":
                                result = await db.execute(
                                    text(
                                        """
                                    SELECT master.get_permissions_for_level(80, 'establishment')
                                """
                                    )
                                )
                                permissions = result.scalar()
                                test_results[func_name]["test_result"] = (
                                    len(permissions) if permissions else 0
                                )
                                logger.info(
                                    f"  ✅ {func_name}: retornou {len(permissions) if permissions else 0} permissões para nível 80"
                                )

                            # Testar função suggest_role_template_for_level
                            elif func_name == "suggest_role_template_for_level":
                                result = await db.execute(
                                    text(
                                        """
                                    SELECT master.suggest_role_template_for_level(80, 'establishment')
                                """
                                    )
                                )
                                template = result.scalar()
                                test_results[func_name]["test_result"] = template
                                logger.info(
                                    f"  ✅ {func_name}: sugeriu template '{template}' para nível 80"
                                )

                        except Exception as e:
                            test_results[func_name]["error"] = str(e)
                            logger.warning(f"  ⚠️ Erro ao testar {func_name}: {e}")
                    else:
                        logger.warning(f"  ❌ Função {func_name} não encontrada")

                return test_results

        except Exception as e:
            logger.error(f"❌ Erro no teste de funções: {e}")
            raise

    async def generate_readiness_report(self) -> Dict[str, Any]:
        """Gerar relatório de prontidão para Fase 2"""
        logger.info("📋 Gerando relatório de prontidão...")

        try:
            async for db in get_db():
                # Estatísticas gerais
                stats = {}

                # Total de permissões mapeadas
                result = await db.execute(
                    text(
                        """
                    SELECT COUNT(DISTINCT permission_name) FROM master.level_permission_mapping
                """
                    )
                )
                stats["unique_permissions"] = result.scalar()

                # Templates ativos
                result = await db.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM master.role_templates WHERE is_active = true
                """
                    )
                )
                stats["active_templates"] = result.scalar()

                # Cobertura de níveis
                result = await db.execute(
                    text(
                        """
                    SELECT
                        MIN(level_min) as lowest_level,
                        MAX(level_max) as highest_level
                    FROM master.level_permission_mapping
                """
                    )
                )
                row = result.fetchone()
                stats["level_coverage"] = f"{row.lowest_level}-{row.highest_level}"

                # Contextos suportados
                result = await db.execute(
                    text(
                        """
                    SELECT COUNT(DISTINCT context_type) FROM master.level_permission_mapping
                """
                    )
                )
                stats["supported_contexts"] = result.scalar()

                logger.info(f"📊 Estatísticas Finais:")
                logger.info(f"  🔑 Permissões únicas: {stats['unique_permissions']}")
                logger.info(f"  📋 Templates ativos: {stats['active_templates']}")
                logger.info(f"  🎚️ Cobertura de níveis: {stats['level_coverage']}")
                logger.info(f"  📍 Contextos suportados: {stats['supported_contexts']}")

                return stats

        except Exception as e:
            logger.error(f"❌ Erro no relatório: {e}")
            raise


async def main():
    """Função principal de validação"""
    logger.info("=" * 60)
    logger.info("🔍 VALIDAÇÃO FASE 1: SETUP DE PERMISSÕES")
    logger.info("=" * 60)

    validator = Phase1Validator()

    try:
        # 1. Validar estrutura do banco
        db_validation = await validator.validate_database_setup()

        # 2. Analisar mapeamentos
        mapping_analysis = await validator.analyze_permission_mappings()

        # 3. Analisar templates
        template_analysis = await validator.analyze_role_templates()

        # 4. Testar funções
        function_tests = await validator.test_permission_functions()

        # 5. Relatório de prontidão
        readiness_stats = await validator.generate_readiness_report()

        # Verificar se tudo está OK
        all_tables_ok = all(db_validation["tables"].values())
        all_indexes_ok = all(db_validation["indexes"].values())
        has_data = all(count > 0 for count in db_validation["data"].values())

        if all_tables_ok and all_indexes_ok and has_data:
            logger.info("🎉 VALIDAÇÃO FASE 1: SUCESSO TOTAL!")
            logger.info("✅ Todas as estruturas foram criadas corretamente")
            logger.info("✅ Dados foram populados com sucesso")
            logger.info("✅ Sistema pronto para Fase 2")
            logger.info("")
            logger.info("📋 Próximos Passos para Fase 2:")
            logger.info("   1. Implementar decorators híbridos nos endpoints")
            logger.info("   2. Migrar APIs de users, companies, establishments")
            logger.info("   3. Testar compatibilidade com sistema atual")
            logger.info("   4. Validar performance do cache")
            return 0
        else:
            logger.error("❌ VALIDAÇÃO FASE 1: PROBLEMAS ENCONTRADOS")
            if not all_tables_ok:
                missing_tables = [
                    k for k, v in db_validation["tables"].items() if not v
                ]
                logger.error(f"   Tabelas faltando: {missing_tables}")
            if not all_indexes_ok:
                missing_indexes = [
                    k for k, v in db_validation["indexes"].items() if not v
                ]
                logger.error(f"   Índices faltando: {missing_indexes}")
            if not has_data:
                empty_tables = [k for k, v in db_validation["data"].items() if v == 0]
                logger.error(f"   Tabelas vazias: {empty_tables}")
            return 1

    except Exception as e:
        logger.error(f"💥 ERRO NA VALIDAÇÃO: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
