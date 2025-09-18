import asyncio
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

from app.infrastructure.cache.decorators import cache_manager
from app.infrastructure.database import get_db
from app.infrastructure.rate_limiting import limiter

logger = structlog.get_logger()
router = APIRouter()


async def check_database(db) -> Dict[str, Any]:
    """Verificar conectividade com banco de dados"""
    try:
        start_time = datetime.utcnow()
        await db.execute(text("SELECT 1"))
        end_time = datetime.utcnow()

        response_time = (end_time - start_time).total_seconds()

        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


async def check_memory() -> Dict[str, Any]:
    """Verificar uso de memória básico"""
    import psutil

    try:
        memory = psutil.virtual_memory()

        return {
            "status": "healthy" if memory.percent < 90 else "warning",
            "usage_percent": memory.percent,
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ImportError:
        return {
            "status": "unavailable",
            "message": "psutil not installed",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get(
    "/health",
    summary="Health Check Básico",
    description="""
    Verificação rápida de status do serviço.

    **Uso:**
    - Load balancers
    - Monitoring básico
    - Status page público

    **Rate limit:** 10 requisições por minuto
    """,
    tags=["Health"],
)
@limiter.limit("10/minute")
async def basic_health_check(request: Request) -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Pro Team Care API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health/detailed",
    summary="Health Check Detalhado",
    description="""
    Verificação completa de todas as dependências do sistema.

    **Verifica:**
    - Conectividade com PostgreSQL
    - Uso de memória do sistema
    - Status do sistema de cache Redis
    - Tempo de resposta de cada componente

    **Rate limit:** 5 requisições por minuto (operação mais custosa)
    """,
    tags=["Health"],
)
@limiter.limit("5/minute")
async def detailed_health_check(request: Request, db=Depends(get_db)) -> Dict[str, Any]:
    start_time = datetime.utcnow()

    # Executar checks em paralelo
    db_check_task = asyncio.create_task(check_database(db))
    memory_check_task = asyncio.create_task(check_memory())
    cache_check_task = asyncio.create_task(cache_manager.cache_health_check())

    # Aguardar todos os checks
    db_result, memory_result, cache_result = await asyncio.gather(
        db_check_task, memory_check_task, cache_check_task, return_exceptions=True
    )

    # Tratar exceções
    if isinstance(db_result, Exception):
        db_result = {
            "status": "error",
            "error": str(db_result),
            "timestamp": datetime.utcnow().isoformat(),
        }

    if isinstance(memory_result, Exception):
        memory_result = {
            "status": "error",
            "error": str(memory_result),
            "timestamp": datetime.utcnow().isoformat(),
        }

    if isinstance(cache_result, Exception):
        cache_result = {
            "status": "error",
            "error": str(cache_result),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Determinar status geral
    components_status = [
        db_result["status"],
        memory_result["status"],
        cache_result["status"],
    ]
    overall_status = "healthy"

    if "unhealthy" in components_status or "error" in components_status:
        overall_status = "unhealthy"
    elif "warning" in components_status:
        overall_status = "warning"

    end_time = datetime.utcnow()
    total_time = (end_time - start_time).total_seconds()

    response = {
        "status": overall_status,
        "service": "Pro Team Care API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(total_time * 1000, 2),
        "checks": {
            "database": db_result,
            "memory": memory_result,
            "cache": cache_result,
        },
    }

    # Log se não estiver saudável
    if overall_status != "healthy":
        logger.warning("Health check failed", response=response)

    return response


@router.get(
    "/live",
    summary="Liveness Probe",
    description="""
    Probe de vitalidade para orquestração Kubernetes.

    **Kubernetes:**
    - Usado para determinar se o pod deve ser reiniciado
    - Resposta rápida sem verificações pesadas
    - Falha apenas se o processo está travado
    """,
    tags=["Health"],
)
async def liveness_probe() -> Dict[str, str]:
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="""
    Probe de prontidão para orquestração Kubernetes.

    **Kubernetes:**
    - Usado para determinar se o pod pode receber tráfego
    - Verifica conectividade com banco de dados
    - Rate limit mais alto (20/min) para uso frequente

    **Status codes:**
    - 200: Pronto para receber requests
    - 503: Não pronto (remover do load balancer)
    """,
    tags=["Health"],
)
@limiter.limit("20/minute")
async def readiness_probe(request: Request, db=Depends(get_db)) -> Dict[str, Any]:
    try:
        # Verificar apenas banco - mais rápido que health detalhado
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get(
    "/cache/stats",
    summary="Estatísticas do Cache",
    description="""
    Métricas detalhadas do sistema de cache Redis.

    **Métricas incluídas:**
    - Hit/miss ratio
    - Número de chaves ativas
    - Uso de memória
    - Estatísticas de performance

    **Uso:**
    - Monitoramento de performance
    - Debugging de cache
    - Otimização de aplicação
    """,
    tags=["Health"],
)
@limiter.limit("10/minute")
async def cache_stats(request: Request) -> Dict[str, Any]:
    try:
        stats = await cache_manager.get_cache_stats()
        return {"timestamp": datetime.utcnow().isoformat(), "cache_stats": stats}
    except Exception as e:
        logger.error("Cache stats failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={"error": str(e), "timestamp": datetime.utcnow().isoformat()},
        )
