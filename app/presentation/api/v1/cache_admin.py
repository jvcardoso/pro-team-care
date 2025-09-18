"""
Cache Administration API - Monitoramento e controle do sistema de cache
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.cache.decorators import cache_manager
from app.infrastructure.cache.simplified_redis import simplified_redis_client

router = APIRouter(tags=["Cache Admin"])


class CacheStatsResponse(BaseModel):
    """Response para estatísticas de cache"""

    hits: int
    misses: int
    hit_rate_percentage: float
    total_requests: int
    memory_used: int
    connected_clients: int
    cache_health: str


class CacheOperationResponse(BaseModel):
    """Response para operações de cache"""

    success: bool
    message: str
    affected_keys: int = 0


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """
    Obtém estatísticas detalhadas do sistema de cache
    Requer autenticação de usuário
    """
    try:
        # Verificar se usuário é admin (opcional - remover se todos podem ver)
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso restrito a administradores",
            )

        # Obter estatísticas do cache
        stats = await cache_manager.get_cache_stats()
        health = await cache_manager.cache_health_check()

        return CacheStatsResponse(
            hits=stats.get("hits", 0),
            misses=stats.get("misses", 0),
            hit_rate_percentage=stats.get("hit_rate_percentage", 0),
            total_requests=stats.get("total_requests", 0),
            memory_used=stats.get("memory_used", 0),
            connected_clients=stats.get("connected_clients", 0),
            cache_health=health.get("status", "unknown"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas do cache: {str(e)}",
        )


@router.post("/cache/clear", response_model=CacheOperationResponse)
async def clear_cache_pattern(
    pattern: str = "*", current_user: User = Depends(get_current_user)
):
    """
    Limpa entradas do cache baseado em padrão

    Args:
        pattern: Padrão para limpeza (ex: "users:*", "menu:*")
    """
    try:
        # Verificar se usuário é admin
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operação restrita a administradores",
            )

        # Limpar cache por padrão
        cleared_count = await simplified_redis_client.clear_pattern(pattern)

        return CacheOperationResponse(
            success=True,
            message=f"Cache limpo com sucesso para padrão: {pattern}",
            affected_keys=cleared_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar cache: {str(e)}",
        )


@router.post("/cache/warm-up", response_model=CacheOperationResponse)
async def warm_up_cache(current_user: User = Depends(get_current_user)):
    """
    Executa pre-aquecimento do cache com dados críticos
    """
    try:
        # Verificar se usuário é admin
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operação restrita a administradores",
            )

        # Lista de funções para pre-aquecer
        cache_functions = [
            {
                "function": get_users_count,  # Referência seria necessária
                "args": (),
                "kwargs": {},
            }
            # Adicionar mais funções conforme necessário
        ]

        # Executar warm-up
        await cache_manager.warm_up_cache(cache_functions)

        return CacheOperationResponse(
            success=True,
            message="Cache pre-aquecido com sucesso",
            affected_keys=len(cache_functions),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no pre-aquecimento do cache: {str(e)}",
        )


@router.get("/cache/health")
async def cache_health_check():
    """
    Verifica saúde do sistema de cache
    Endpoint público para monitoramento
    """
    try:
        health = await cache_manager.cache_health_check()

        return {
            "cache_status": health.get("status", "unknown"),
            "connected": health.get("connected", False),
            "timestamp": "2025-09-10T17:15:00Z",
            "service": "Pro Team Care Cache",
        }

    except Exception as e:
        return {
            "cache_status": "error",
            "connected": False,
            "error": str(e),
            "timestamp": "2025-09-10T17:15:00Z",
            "service": "Pro Team Care Cache",
        }


@router.get("/cache/keys", response_model=Dict[str, Any])
async def list_cache_keys(
    pattern: str = "*", limit: int = 100, current_user: User = Depends(get_current_user)
):
    """
    Lista chaves do cache (para debug)

    Args:
        pattern: Padrão de busca
        limit: Limite de resultados
    """
    try:
        # Verificar se usuário é admin
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operação restrita a administradores",
            )

        # Buscar chaves
        if simplified_redis_client.redis:
            keys = await simplified_redis_client.redis.keys(pattern)
            # Limitar resultados
            keys = keys[:limit] if keys else []

            return {
                "pattern": pattern,
                "total_found": len(keys),
                "showing": min(len(keys), limit),
                "keys": [
                    key.decode() if isinstance(key, bytes) else key for key in keys
                ],
            }
        else:
            return {
                "pattern": pattern,
                "total_found": 0,
                "showing": 0,
                "keys": [],
                "error": "Redis não conectado",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar chaves: {str(e)}",
        )
