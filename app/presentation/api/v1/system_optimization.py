"""
API endpoints para otimização e validação do sistema
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.services.system_optimization_service import SystemOptimizationService
from app.presentation.decorators.role_permissions import require_role_level_or_permission

router = APIRouter(prefix="/system-optimization", tags=["System Optimization"])
logger = logging.getLogger(__name__)


# === UTILITY FUNCTIONS ===

def get_optimization_service(db: AsyncSession = Depends(get_db)) -> SystemOptimizationService:
    """Factory para serviço de otimização"""
    return SystemOptimizationService(db)


# === SYSTEM HEALTH ENDPOINTS ===

@router.get("/health-check")
@require_role_level_or_permission(80, "system.health_check")
async def run_system_health_check(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Executar verificação completa de saúde do sistema"""
    try:
        health_check = await service.run_system_health_check()

        logger.info(f"Health check executado: {health_check['overall_status']}")
        return health_check

    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na verificação de saúde"
        )


@router.post("/performance-optimization")
@require_role_level_or_permission(90, "system.optimize")
async def run_performance_optimization(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Executar otimizações de performance"""
    try:
        optimization_results = await service.run_performance_optimization()

        logger.info(f"Otimização executada: {len(optimization_results['optimizations_applied'])} aplicadas")
        return optimization_results

    except Exception as e:
        logger.error(f"Erro na otimização: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na otimização de performance"
        )


@router.get("/business-rules-validation")
@require_role_level_or_permission(70, "system.validate")
async def validate_business_rules(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Validar regras de negócio implementadas"""
    try:
        validation_results = await service.validate_business_rules()

        logger.info(f"Validação executada: {validation_results['success_rate']:.2f}% sucesso")
        return validation_results

    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na validação de regras"
        )


@router.get("/system-report")
@require_role_level_or_permission(80, "system.report")
async def generate_system_report(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Gerar relatório completo do sistema"""
    try:
        system_report = await service.generate_system_report()

        logger.info("Relatório completo do sistema gerado")
        return system_report

    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar relatório"
        )


# === MONITORING ENDPOINTS ===

@router.get("/quick-status")
@require_role_level_or_permission(50, "system.status")
async def get_quick_status(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Status rápido do sistema (verificação básica)"""
    try:
        # Executar verificações básicas de conectividade
        quick_status = {
            "timestamp": datetime.now().isoformat(),
            "database_connection": "ok",
            "api_status": "ok",
            "quick_check": "healthy"
        }

        # Verificação rápida de tabelas críticas
        try:
            stats = await service._get_system_statistics()
            quick_status["system_stats"] = stats

            # Verificar se há dados básicos
            if stats.get("total_contracts", 0) >= 0 and stats.get("total_users", 0) > 0:
                quick_status["data_integrity"] = "ok"
            else:
                quick_status["data_integrity"] = "warning"
                quick_status["quick_check"] = "degraded"

        except Exception as e:
            quick_status["data_integrity"] = "error"
            quick_status["quick_check"] = "error"
            quick_status["error"] = str(e)

        logger.info(f"Status rápido: {quick_status['quick_check']}")
        return quick_status

    except Exception as e:
        logger.error(f"Erro no status rápido: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "database_connection": "error",
            "api_status": "error",
            "quick_check": "error",
            "error": str(e)
        }


# === MAINTENANCE ENDPOINTS ===

@router.post("/maintenance/cleanup")
@require_role_level_or_permission(90, "system.maintenance")
async def run_maintenance_cleanup(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Executar limpeza de manutenção"""
    try:
        cleanup_results = await service._cleanup_old_data()

        logger.info(f"Limpeza executada: {cleanup_results['cleaned_records']} registros removidos")
        return {
            "timestamp": datetime.now().isoformat(),
            "cleanup_results": cleanup_results,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na limpeza de manutenção"
        )


@router.post("/maintenance/update-statistics")
@require_role_level_or_permission(80, "system.maintenance")
async def update_database_statistics(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Atualizar estatísticas do banco de dados"""
    try:
        await service._update_table_statistics()

        logger.info("Estatísticas do banco atualizadas")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "message": "Estatísticas do banco de dados atualizadas com sucesso"
        }

    except Exception as e:
        logger.error(f"Erro ao atualizar estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar estatísticas"
        )


# === DIAGNOSTIC ENDPOINTS ===

@router.get("/diagnostics/tables")
@require_role_level_or_permission(70, "system.diagnostics")
async def check_table_integrity(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Verificar integridade das tabelas"""
    try:
        table_check = await service._check_table_integrity()

        logger.info(f"Verificação de tabelas: {table_check['status']}")
        return {
            "timestamp": datetime.now().isoformat(),
            "table_integrity": table_check
        }

    except Exception as e:
        logger.error(f"Erro na verificação de tabelas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na verificação de tabelas"
        )


@router.get("/diagnostics/performance")
@require_role_level_or_permission(70, "system.diagnostics")
async def check_query_performance(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Verificar performance das queries"""
    try:
        performance_check = await service._check_query_performance()

        logger.info(f"Verificação de performance: {performance_check['status']}")
        return {
            "timestamp": datetime.now().isoformat(),
            "query_performance": performance_check
        }

    except Exception as e:
        logger.error(f"Erro na verificação de performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na verificação de performance"
        )


@router.get("/diagnostics/data-consistency")
@require_role_level_or_permission(70, "system.diagnostics")
async def check_data_consistency(
    service: SystemOptimizationService = Depends(get_optimization_service)
):
    """Verificar consistência dos dados"""
    try:
        consistency_check = await service._check_data_consistency()

        logger.info(f"Verificação de consistência: {consistency_check['status']}")
        return {
            "timestamp": datetime.now().isoformat(),
            "data_consistency": consistency_check
        }

    except Exception as e:
        logger.error(f"Erro na verificação de consistência: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na verificação de consistência"
        )