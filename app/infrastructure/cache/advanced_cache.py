"""
Advanced Multi-Layer Cache System com Invalidação Inteligente
"""

import asyncio
import hashlib
import json
import time
import weakref
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Union

import structlog

from app.infrastructure.cache.simplified_redis import (
    SerializationMethod,
    SimplifiedRedisClient,
)

logger = structlog.get_logger()


@dataclass
class CacheMetrics:
    """Métricas de performance do cache"""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_response_time_ms: float = 0

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0

    @property
    def l1_efficiency(self) -> float:
        return (
            (self.l1_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        )


@dataclass
class CacheEntry:
    """Entrada do cache com metadados"""

    value: Any
    created_at: float
    expires_at: Optional[float]
    tags: Set[str] = field(default_factory=set)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return self.expires_at is not None and time.time() > self.expires_at

    def touch(self):
        """Atualiza último acesso"""
        self.access_count += 1
        self.last_accessed = time.time()


class AdvancedCacheManager:
    """Sistema de cache avançado em múltiplas camadas"""

    def __init__(
        self,
        redis_client: Optional[SimplifiedRedisClient] = None,
        l1_max_size: int = 1000,
        l1_ttl_seconds: int = 300,
        l2_default_ttl: int = 3600,
        enable_metrics: bool = True,
    ):
        self.redis_client = redis_client or SimplifiedRedisClient()
        self.l1_max_size = l1_max_size
        self.l1_ttl_seconds = l1_ttl_seconds
        self.l2_default_ttl = l2_default_ttl
        self.enable_metrics = enable_metrics

        # L1 Cache (In-Memory)
        self._l1_cache: Dict[str, CacheEntry] = {}
        self._l1_access_order: List[str] = []

        # Tag management
        self._tag_to_keys: Dict[str, Set[str]] = defaultdict(set)
        self._key_to_tags: Dict[str, Set[str]] = defaultdict(set)

        # Metrics
        self.metrics = CacheMetrics() if enable_metrics else None

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warmup_tasks: Set[asyncio.Task] = set()

        # Lock para operações thread-safe
        self._lock = asyncio.Lock()

    async def start(self):
        """Inicia o sistema de cache"""
        try:
            await self.redis_client.connect()
            logger.info("🚀 Advanced Cache Manager iniciado com sucesso")

            # Iniciar tarefas em background
            self._cleanup_task = asyncio.create_task(self._cleanup_background())

        except Exception as e:
            logger.warning(f"⚠️ Cache Redis indisponível, usando apenas L1: {e}")

    async def stop(self):
        """Para o sistema de cache"""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        for task in self._warmup_tasks:
            task.cancel()

        await self.redis_client.disconnect()
        logger.info("🛑 Advanced Cache Manager parado")

    def _generate_key(self, namespace: str, key: str) -> str:
        """Gera chave única para o cache"""
        return f"advanced_cache:{namespace}:{key}"

    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho aproximado do objeto em bytes"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode("utf-8") if isinstance(value, str) else value)
            return len(json.dumps(value, default=str).encode("utf-8"))
        except:
            return 64  # Tamanho estimado padrão

    async def get(
        self,
        namespace: str,
        key: str,
        default: Any = None,
        deserializer: Optional[Callable] = None,
    ) -> Any:
        """Obtém valor do cache (L1 -> L2)"""
        start_time = time.time()
        cache_key = self._generate_key(namespace, key)

        try:
            async with self._lock:
                # L1 Cache check
                if cache_key in self._l1_cache:
                    entry = self._l1_cache[cache_key]
                    if not entry.is_expired():
                        entry.touch()
                        self._update_access_order(cache_key)
                        if self.metrics:
                            self.metrics.hits += 1
                            self.metrics.l1_hits += 1
                            self.metrics.total_requests += 1

                        logger.debug(f"📋 L1 Cache HIT: {namespace}:{key}")
                        return entry.value
                    else:
                        # Remove expired entry
                        await self._remove_from_l1(cache_key)

                # L2 Cache check (Redis)
                if self.redis_client.redis:
                    try:
                        redis_value = await self.redis_client.get(cache_key)
                        if redis_value is not None:
                            # Deserializar se necessário
                            value = (
                                deserializer(redis_value)
                                if deserializer
                                else redis_value
                            )

                            # Adicionar de volta ao L1
                            await self._add_to_l1(
                                cache_key, value, ttl_seconds=self.l1_ttl_seconds
                            )

                            if self.metrics:
                                self.metrics.hits += 1
                                self.metrics.l2_hits += 1
                                self.metrics.total_requests += 1

                            logger.debug(f"📡 L2 Cache HIT: {namespace}:{key}")
                            return value
                    except Exception as e:
                        logger.warning(f"⚠️ L2 Cache error: {e}")

                # Cache MISS
                if self.metrics:
                    self.metrics.misses += 1
                    self.metrics.total_requests += 1

                logger.debug(f"❌ Cache MISS: {namespace}:{key}")
                return default

        finally:
            # Atualizar métricas de tempo
            if self.metrics:
                response_time = (time.time() - start_time) * 1000
                total = self.metrics.total_requests
                self.metrics.avg_response_time_ms = (
                    self.metrics.avg_response_time_ms * (total - 1) + response_time
                ) / total

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        serializer: Optional[Callable] = None,
        l1_only: bool = False,
    ) -> bool:
        """Define valor no cache (L1 + L2)"""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl_seconds or self.l2_default_ttl
        tags = tags or set()

        try:
            async with self._lock:
                # L1 Cache
                await self._add_to_l1(cache_key, value, ttl_seconds=ttl, tags=tags)

                # L2 Cache (Redis) - opcional
                if not l1_only and self.redis_client.redis:
                    try:
                        # Serializar se necessário
                        redis_value = serializer(value) if serializer else value
                        await self.redis_client.set(
                            cache_key,
                            redis_value,
                            ttl_seconds=ttl,
                            serialization=SerializationMethod.JSON,
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ L2 Cache set error: {e}")

                # Atualizar tags
                self._update_tags(cache_key, tags)

                if self.metrics:
                    self.metrics.sets += 1

                logger.debug(
                    f"💾 Cache SET: {namespace}:{key} TTL: {ttl}s Tags: {tags}"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Cache SET error: {e}")
            return False

    async def delete(self, namespace: str, key: str) -> bool:
        """Remove valor do cache"""
        cache_key = self._generate_key(namespace, key)

        try:
            async with self._lock:
                # L1 Cache
                removed_l1 = await self._remove_from_l1(cache_key)

                # L2 Cache
                removed_l2 = False
                if self.redis_client.redis:
                    try:
                        removed_l2 = await self.redis_client.delete(cache_key)
                    except Exception as e:
                        logger.warning(f"⚠️ L2 Cache delete error: {e}")

                if self.metrics:
                    self.metrics.deletes += 1

                logger.debug(f"🗑️ Cache DELETE: {namespace}:{key}")
                return removed_l1 or removed_l2

        except Exception as e:
            logger.error(f"❌ Cache DELETE error: {e}")
            return False

    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalida todas as entradas com as tags especificadas"""
        invalidated_count = 0

        try:
            async with self._lock:
                keys_to_remove = set()

                for tag in tags:
                    keys_to_remove.update(self._tag_to_keys.get(tag, set()))

                # Remover do L1
                for cache_key in keys_to_remove:
                    if await self._remove_from_l1(cache_key):
                        invalidated_count += 1

                    # Remover do L2
                    if self.redis_client.redis:
                        try:
                            await self.redis_client.delete(cache_key)
                        except Exception as e:
                            logger.warning(f"⚠️ L2 invalidation error: {e}")

                logger.info(
                    f"🔄 Cache invalidated by tags {tags}: {invalidated_count} entries"
                )
                return invalidated_count

        except Exception as e:
            logger.error(f"❌ Tag invalidation error: {e}")
            return 0

    async def clear_namespace(self, namespace: str) -> int:
        """Limpa todo o cache de um namespace"""
        prefix = f"advanced_cache:{namespace}:"
        cleared_count = 0

        try:
            async with self._lock:
                # L1 Cache
                keys_to_remove = [
                    k for k in self._l1_cache.keys() if k.startswith(prefix)
                ]
                for cache_key in keys_to_remove:
                    if await self._remove_from_l1(cache_key):
                        cleared_count += 1

                # L2 Cache - pattern delete
                if self.redis_client.redis:
                    try:
                        pattern = f"{prefix}*"
                        keys = await self.redis_client.redis.keys(pattern)
                        if keys:
                            await self.redis_client.redis.delete(*keys)
                    except Exception as e:
                        logger.warning(f"⚠️ L2 namespace clear error: {e}")

                logger.info(
                    f"🧹 Namespace '{namespace}' cleared: {cleared_count} entries"
                )
                return cleared_count

        except Exception as e:
            logger.error(f"❌ Namespace clear error: {e}")
            return 0

    async def warm_cache(
        self,
        namespace: str,
        warm_func: Callable,
        keys: List[str],
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
    ):
        """Pre-aquece o cache com dados"""

        async def warm_single_key(key: str):
            try:
                value = await warm_func(key)
                if value is not None:
                    await self.set(namespace, key, value, ttl_seconds, tags)
                    logger.debug(f"🔥 Cache warmed: {namespace}:{key}")
            except Exception as e:
                logger.warning(f"⚠️ Cache warm error for {key}: {e}")

        # Executar em paralelo com limite de concorrência
        semaphore = asyncio.Semaphore(10)

        async def limited_warm(key: str):
            async with semaphore:
                await warm_single_key(key)

        tasks = [asyncio.create_task(limited_warm(key)) for key in keys]
        self._warmup_tasks.update(tasks)

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(
                f"🔥 Cache warming completed for namespace '{namespace}': {len(keys)} keys"
            )
        finally:
            for task in tasks:
                self._warmup_tasks.discard(task)

    async def _add_to_l1(
        self,
        cache_key: str,
        value: Any,
        ttl_seconds: int,
        tags: Optional[Set[str]] = None,
    ):
        """Adiciona entrada ao L1 cache"""
        # Evictions se necessário
        while len(self._l1_cache) >= self.l1_max_size:
            await self._evict_lru()

        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        size_bytes = self._calculate_size(value)

        entry = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
            tags=tags or set(),
            size_bytes=size_bytes,
        )

        self._l1_cache[cache_key] = entry
        self._update_access_order(cache_key)

    async def _remove_from_l1(self, cache_key: str) -> bool:
        """Remove entrada do L1 cache"""
        if cache_key in self._l1_cache:
            del self._l1_cache[cache_key]
            if cache_key in self._l1_access_order:
                self._l1_access_order.remove(cache_key)

            # Limpar tags
            self._cleanup_tags(cache_key)
            return True
        return False

    def _update_access_order(self, cache_key: str):
        """Atualiza ordem de acesso para LRU"""
        if cache_key in self._l1_access_order:
            self._l1_access_order.remove(cache_key)
        self._l1_access_order.append(cache_key)

    async def _evict_lru(self):
        """Remove entrada menos recentemente usada"""
        if self._l1_access_order:
            oldest_key = self._l1_access_order[0]
            await self._remove_from_l1(oldest_key)
            if self.metrics:
                self.metrics.evictions += 1

    def _update_tags(self, cache_key: str, tags: Set[str]):
        """Atualiza mapeamento de tags"""
        # Limpar tags antigas
        old_tags = self._key_to_tags.get(cache_key, set())
        for old_tag in old_tags:
            self._tag_to_keys[old_tag].discard(cache_key)

        # Adicionar novas tags
        self._key_to_tags[cache_key] = tags
        for tag in tags:
            self._tag_to_keys[tag].add(cache_key)

    def _cleanup_tags(self, cache_key: str):
        """Limpa tags de uma chave removida"""
        tags = self._key_to_tags.get(cache_key, set())
        for tag in tags:
            self._tag_to_keys[tag].discard(cache_key)
        self._key_to_tags.pop(cache_key, None)

    async def _cleanup_background(self):
        """Tarefa background para limpeza de expirados"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = time.time()
                expired_keys = []

                async with self._lock:
                    for cache_key, entry in self._l1_cache.items():
                        if entry.is_expired():
                            expired_keys.append(cache_key)

                    for cache_key in expired_keys:
                        await self._remove_from_l1(cache_key)

                if expired_keys:
                    logger.debug(
                        f"🧹 Cleanup: removed {len(expired_keys)} expired entries"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Background cleanup error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        l1_total_size = sum(entry.size_bytes for entry in self._l1_cache.values())

        return {
            "metrics": {
                "hit_ratio": self.metrics.hit_ratio if self.metrics else 0,
                "l1_efficiency": self.metrics.l1_efficiency if self.metrics else 0,
                "total_requests": self.metrics.total_requests if self.metrics else 0,
                "avg_response_time_ms": (
                    round(self.metrics.avg_response_time_ms, 2) if self.metrics else 0
                ),
                "hits": self.metrics.hits if self.metrics else 0,
                "misses": self.metrics.misses if self.metrics else 0,
                "l1_hits": self.metrics.l1_hits if self.metrics else 0,
                "l2_hits": self.metrics.l2_hits if self.metrics else 0,
                "evictions": self.metrics.evictions if self.metrics else 0,
            },
            "l1_cache": {
                "size": len(self._l1_cache),
                "max_size": self.l1_max_size,
                "total_size_bytes": l1_total_size,
                "utilization": len(self._l1_cache) / self.l1_max_size * 100,
            },
            "tags": {
                "unique_tags": len(self._tag_to_keys),
                "tagged_keys": len(self._key_to_tags),
            },
        }


# Instância global
advanced_cache: Optional[AdvancedCacheManager] = None


async def get_advanced_cache() -> AdvancedCacheManager:
    """Factory function para o cache avançado"""
    global advanced_cache
    if advanced_cache is None:
        advanced_cache = AdvancedCacheManager()
        await advanced_cache.start()
    return advanced_cache
