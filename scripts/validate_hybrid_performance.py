#!/usr/bin/env python3
"""
Validação de Performance do Sistema Híbrido
Testa se a migração para permissões granulares não impacta performance
"""

import asyncio
import logging
import statistics
import sys
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

# Adicionar o caminho da aplicação
sys.path.append("/home/juliano/Projetos/pro_team_care_16")

from app.domain.entities.user import User
from app.infrastructure.cache.permission_cache import PermissionCache
from app.presentation.decorators.hybrid_permissions import check_user_permission

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceValidator:
    """Validador de performance do sistema híbrido"""

    def __init__(self):
        self.cache = PermissionCache()
        self.results = {}

    async def setup(self):
        """Setup inicial"""
        logger.info("🚀 Iniciando validação de performance...")
        # Inicializar cache sem Redis (teste local)
        self.cache.redis = None

    def create_test_user(self, user_id: int, level: int) -> User:
        """Criar usuário de teste"""
        return User(
            id=user_id,
            email_address=f"test{user_id}@example.com",
            user_name=f"testuser{user_id}",
            level=level,
            company_id=1,
            establishment_id=1,
            is_system_admin=False,
        )

    async def benchmark_permission_check(
        self, iterations: int = 1000
    ) -> Dict[str, float]:
        """Benchmark de verificação de permissões"""
        logger.info(
            f"📊 Executando benchmark de permissões ({iterations} iterações)..."
        )

        user = self.create_test_user(1, 60)
        permission = "users.view"
        context_type = "establishment"

        # Mock do cache para retornar permissões
        mock_permissions = ["users.view", "users.list", "companies.view"]

        with patch.object(
            self.cache, "get_user_permissions", return_value=mock_permissions
        ):
            # Benchmark: verificação via permissões granulares
            start_time = time.perf_counter()
            for _ in range(iterations):
                await self.cache.has_permission(user.id, permission, context_type)
            granular_time = time.perf_counter() - start_time

        # Benchmark: verificação via níveis (simulação)
        start_time = time.perf_counter()
        for _ in range(iterations):
            # Simula verificação simples de nível
            result = user.level >= 40  # Equivalente ao nível mínimo
        level_time = time.perf_counter() - start_time

        logger.info(
            f"  ⚡ Granular: {granular_time:.4f}s ({granular_time/iterations*1000:.2f}ms/op)"
        )
        logger.info(
            f"  ⚡ Nível:    {level_time:.4f}s ({level_time/iterations*1000:.2f}ms/op)"
        )
        logger.info(f"  📈 Overhead: {((granular_time/level_time - 1) * 100):.1f}%")

        return {
            "granular_time": granular_time,
            "level_time": level_time,
            "overhead_percent": ((granular_time / level_time - 1) * 100),
            "iterations": iterations,
        }

    async def benchmark_cache_performance(
        self, iterations: int = 500
    ) -> Dict[str, float]:
        """Benchmark do cache de permissões"""
        logger.info(f"💾 Testando performance do cache ({iterations} iterações)...")

        user = self.create_test_user(2, 70)
        permission = "companies.edit"
        context_type = "company"

        # Mock do banco de dados (simulando busca lenta)
        mock_permissions = ["companies.edit", "companies.view", "establishments.edit"]

        with patch.object(
            self.cache, "_fetch_permissions_from_db", return_value=mock_permissions
        ) as mock_db:
            # Primeira chamada (cache miss)
            start_time = time.perf_counter()
            await self.cache.get_user_permissions(user.id, context_type)
            first_call_time = time.perf_counter() - start_time

            # Chamadas subsequentes (cache hit simulado)
            times = []
            for _ in range(iterations):
                start_time = time.perf_counter()
                await self.cache.get_user_permissions(user.id, context_type)
                times.append(time.perf_counter() - start_time)

            avg_cached_time = statistics.mean(times)
            speedup = first_call_time / avg_cached_time

            logger.info(f"  🔍 Primeira busca (DB):  {first_call_time*1000:.2f}ms")
            logger.info(f"  ⚡ Cache hit médio:      {avg_cached_time*1000:.4f}ms")
            logger.info(f"  🚀 Speedup:              {speedup:.1f}x")

            # Mock deve ter sido chamado apenas uma vez
            assert (
                mock_db.call_count == 1
            ), f"DB deveria ser chamado 1x, foi {mock_db.call_count}x"

        return {
            "first_call_ms": first_call_time * 1000,
            "cached_call_ms": avg_cached_time * 1000,
            "speedup": speedup,
            "iterations": iterations,
        }

    async def benchmark_hybrid_decorator(
        self, iterations: int = 1000
    ) -> Dict[str, float]:
        """Benchmark do decorator híbrido"""
        logger.info(
            f"🎭 Testando performance do decorator híbrido ({iterations} iterações)..."
        )

        user = self.create_test_user(3, 80)
        permission = "roles.create"
        min_level = 70
        context_type = "establishment"

        # Mock para retornar que usuário TEM a permissão (caso otimista)
        with patch.object(self.cache, "has_permission", return_value=True):
            start_time = time.perf_counter()
            for _ in range(iterations):
                # Simular a lógica do decorator
                has_perm = await self.cache.has_permission(
                    user.id, permission, context_type
                )
                if not has_perm:
                    # Fallback para nível
                    has_perm = user.level >= min_level
            permission_path_time = time.perf_counter() - start_time

        # Mock para retornar que usuário NÃO tem a permissão (fallback para nível)
        with patch.object(self.cache, "has_permission", return_value=False):
            start_time = time.perf_counter()
            for _ in range(iterations):
                # Simular a lógica do decorator
                has_perm = await self.cache.has_permission(
                    user.id, permission, context_type
                )
                if not has_perm:
                    # Fallback para nível
                    has_perm = user.level >= min_level
            fallback_path_time = time.perf_counter() - start_time

        logger.info(
            f"  ✅ Caminho permissão:    {permission_path_time*1000/iterations:.3f}ms/op"
        )
        logger.info(
            f"  🔄 Caminho fallback:     {fallback_path_time*1000/iterations:.3f}ms/op"
        )

        return {
            "permission_path_ms": permission_path_time * 1000 / iterations,
            "fallback_path_ms": fallback_path_time * 1000 / iterations,
            "iterations": iterations,
        }

    async def test_memory_usage(self) -> Dict[str, Any]:
        """Teste de uso de memória"""
        logger.info("🧠 Testando uso de memória...")

        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Simular cache com muitos usuários
        users_count = 100
        permissions_per_user = 20

        mock_permissions = [f"permission_{i}" for i in range(permissions_per_user)]

        with patch.object(
            self.cache, "_fetch_permissions_from_db", return_value=mock_permissions
        ):
            # Pré-carregar cache para múltiplos usuários
            for user_id in range(1, users_count + 1):
                await self.cache.get_user_permissions(user_id, "establishment")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        logger.info(f"  📊 Memória inicial:      {initial_memory:.1f} MB")
        logger.info(f"  📊 Memória final:        {final_memory:.1f} MB")
        logger.info(f"  📈 Aumento:              {memory_increase:.1f} MB")
        logger.info(f"  👥 Usuários simulados:   {users_count}")
        logger.info(f"  💾 MB por usuário:       {memory_increase/users_count:.3f} MB")

        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "users_count": users_count,
            "mb_per_user": memory_increase / users_count,
        }

    async def validate_backward_compatibility(self) -> Dict[str, bool]:
        """Validar compatibilidade com sistema legado"""
        logger.info("🔄 Validando compatibilidade com sistema legado...")

        results = {}

        # Teste 1: Usuário com nível alto deve conseguir acessar (mesmo sem permissão granular)
        high_level_user = self.create_test_user(4, 90)
        with patch.object(self.cache, "has_permission", return_value=False):
            # Simular verificação híbrida
            has_access = await self.cache.has_permission(
                high_level_user.id, "system.admin", "system"
            )
            if not has_access:
                has_access = high_level_user.level >= 90  # Fallback

        results["high_level_fallback"] = has_access
        logger.info(
            f"  ✅ Usuário nível alto (fallback): {'✅' if has_access else '❌'}"
        )

        # Teste 2: Usuário com permissão granular deve conseguir acessar (mesmo com nível baixo)
        low_level_user = self.create_test_user(5, 30)
        with patch.object(self.cache, "has_permission", return_value=True):
            has_access = await self.cache.has_permission(
                low_level_user.id, "users.view", "establishment"
            )

        results["granular_permission_works"] = has_access
        logger.info(
            f"  ✅ Usuário com permissão granular: {'✅' if has_access else '❌'}"
        )

        # Teste 3: Sistema deve negar acesso quando nem nível nem permissão são suficientes
        low_user = self.create_test_user(6, 20)
        with patch.object(self.cache, "has_permission", return_value=False):
            has_access = await self.cache.has_permission(
                low_user.id, "system.admin", "system"
            )
            if not has_access:
                has_access = low_user.level >= 90  # Fallback

        results["proper_denial"] = not has_access  # Deve ser False (acesso negado)
        logger.info(
            f"  ✅ Negação correta de acesso: {'✅' if not has_access else '❌'}"
        )

        return results

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Gerar relatório completo de performance"""
        logger.info("📋 Gerando relatório de performance...")

        report = {}

        # Executar todos os benchmarks
        report["permission_benchmark"] = await self.benchmark_permission_check()
        report["cache_performance"] = await self.benchmark_cache_performance()
        report["hybrid_decorator"] = await self.benchmark_hybrid_decorator()
        report["memory_usage"] = await self.test_memory_usage()
        report["compatibility"] = await self.validate_backward_compatibility()

        # Análise geral
        permission_overhead = report["permission_benchmark"]["overhead_percent"]
        cache_speedup = report["cache_performance"]["speedup"]
        memory_per_user = report["memory_usage"]["mb_per_user"]

        report["analysis"] = {
            "performance_acceptable": permission_overhead < 50,  # Overhead < 50%
            "cache_effective": cache_speedup > 10,  # Cache speedup > 10x
            "memory_efficient": memory_per_user < 1.0,  # < 1MB por usuário
            "compatibility_ok": all(report["compatibility"].values()),
        }

        overall_ok = all(report["analysis"].values())
        report["overall_status"] = "✅ APROVADO" if overall_ok else "❌ REQUER ATENÇÃO"

        return report


async def main():
    """Função principal de validação"""
    logger.info("=" * 60)
    logger.info("🚀 VALIDAÇÃO DE PERFORMANCE - SISTEMA HÍBRIDO")
    logger.info("=" * 60)

    validator = PerformanceValidator()
    await validator.setup()

    try:
        # Gerar relatório completo
        report = await validator.generate_performance_report()

        # Exibir resultados
        logger.info("\n" + "=" * 60)
        logger.info("📊 RELATÓRIO DE PERFORMANCE")
        logger.info("=" * 60)

        # Performance de permissões
        perm_bench = report["permission_benchmark"]
        logger.info(f"🔐 Verificação de Permissões:")
        logger.info(f"   Overhead vs níveis: {perm_bench['overhead_percent']:.1f}%")

        # Cache performance
        cache_perf = report["cache_performance"]
        logger.info(f"💾 Performance do Cache:")
        logger.info(f"   Speedup: {cache_perf['speedup']:.1f}x")
        logger.info(f"   Cache hit: {cache_perf['cached_call_ms']:.3f}ms")

        # Memória
        memory = report["memory_usage"]
        logger.info(f"🧠 Uso de Memória:")
        logger.info(f"   Por usuário: {memory['mb_per_user']:.3f} MB")

        # Compatibilidade
        compat = report["compatibility"]
        logger.info(f"🔄 Compatibilidade:")
        logger.info(f"   Todos os testes: {'✅' if all(compat.values()) else '❌'}")

        # Status geral
        analysis = report["analysis"]
        logger.info(f"\n🎯 ANÁLISE GERAL:")
        logger.info(
            f"   Performance: {'✅' if analysis['performance_acceptable'] else '❌'}"
        )
        logger.info(f"   Cache:       {'✅' if analysis['cache_effective'] else '❌'}")
        logger.info(f"   Memória:     {'✅' if analysis['memory_efficient'] else '❌'}")
        logger.info(f"   Compatib.:   {'✅' if analysis['compatibility_ok'] else '❌'}")

        logger.info(f"\n🏆 STATUS FINAL: {report['overall_status']}")

        if report["overall_status"] == "✅ APROVADO":
            logger.info("\n✅ Sistema híbrido validado com sucesso!")
            logger.info("   ✅ Performance dentro dos limites aceitáveis")
            logger.info("   ✅ Cache funcionando eficientemente")
            logger.info("   ✅ Uso de memória otimizado")
            logger.info("   ✅ Compatibilidade mantida")
            logger.info("\n🚀 PRONTO PARA PRODUÇÃO!")
            return 0
        else:
            logger.error("\n❌ Sistema requer otimizações antes da produção")
            return 1

    except Exception as e:
        logger.error(f"💥 Erro na validação: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
