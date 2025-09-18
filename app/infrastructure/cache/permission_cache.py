"""
Sistema de Cache de Permissões
Cache otimizado para verificação rápida de permissões granulares
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as aioredis
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from config.settings import settings

logger = structlog.get_logger()


class PermissionCache:
    """
    Cache inteligente de permissões por usuário com Redis
    Otimizado para performance e consistência
    """

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.cache_ttl = 1800  # 30 minutos
        self.batch_size = 100
        self._connection_pool = None

    async def init_redis(self):
        """Inicializar conexão Redis"""
        try:
            if not self.redis:
                # Configuração do pool de conexões
                self._connection_pool = aioredis.ConnectionPool.from_url(
                    f"redis://{settings.redis_host}:{settings.redis_port}",
                    decode_responses=True,
                    max_connections=20,
                )
                self.redis = aioredis.Redis(connection_pool=self._connection_pool)

                # Testar conexão
                await self.redis.ping()
                logger.info("✅ Redis conectado para cache de permissões")

        except Exception as e:
            logger.error(f"❌ Erro ao conectar Redis: {e}")
            # Fallback para cache em memória se Redis não disponível
            self.redis = None

    async def close_redis(self):
        """Fechar conexão Redis"""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()

    def _get_cache_key(
        self, user_id: int, context_type: str, context_id: Optional[int] = None
    ) -> str:
        """Gerar chave de cache padronizada"""
        if context_id:
            return f"permissions:user:{user_id}:ctx:{context_type}:{context_id}"
        return f"permissions:user:{user_id}:ctx:{context_type}"

    def _get_user_cache_pattern(self, user_id: int) -> str:
        """Padrão para invalidar todo cache do usuário"""
        return f"permissions:user:{user_id}:*"

    async def get_user_permissions(
        self,
        user_id: int,
        context_type: str,
        context_id: Optional[int] = None,
        force_refresh: bool = False,
    ) -> List[str]:
        """
        Buscar todas as permissões do usuário em um contexto específico
        """
        try:
            cache_key = self._get_cache_key(user_id, context_type, context_id)

            # Verificar cache se não forçar refresh
            if not force_refresh and self.redis:
                try:
                    cached_data = await self.redis.get(cache_key)
                    if cached_data:
                        permissions = json.loads(cached_data)
                        logger.debug(
                            "🎯 Cache hit para permissões",
                            user_id=user_id,
                            context_type=context_type,
                            permissions_count=len(permissions),
                        )
                        return permissions
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(f"⚠️ Erro ao ler cache: {e}")

            # Buscar no banco de dados
            permissions = await self._fetch_permissions_from_db(
                user_id, context_type, context_id
            )

            # Cachear resultado
            if self.redis:
                try:
                    await self.redis.setex(
                        cache_key, self.cache_ttl, json.dumps(permissions)
                    )
                    logger.debug(
                        "💾 Permissões cacheadas",
                        user_id=user_id,
                        context_type=context_type,
                        permissions_count=len(permissions),
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao cachear: {e}")

            return permissions

        except Exception as e:
            logger.error(
                f"❌ Erro ao buscar permissões",
                user_id=user_id,
                context_type=context_type,
                error=str(e),
            )
            return []

    async def _fetch_permissions_from_db(
        self, user_id: int, context_type: str, context_id: Optional[int] = None
    ) -> List[str]:
        """Buscar permissões diretamente do banco"""
        try:
            async for db in get_db():
                # Construir query dinamicamente para evitar problemas com NULL
                if context_id is None:
                    query = text(
                        """
                        SELECT DISTINCT p.name
                        FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        JOIN master.role_permissions rp ON r.id = rp.role_id
                        JOIN master.permissions p ON rp.permission_id = p.id
                        WHERE ur.user_id = :user_id
                          AND ur.context_type = :context_type
                          AND ur.status = 'active'
                          AND ur.deleted_at IS NULL
                          AND r.is_active = true
                          AND p.is_active = true
                        ORDER BY p.name
                    """
                    )
                    params = {"user_id": user_id, "context_type": context_type}
                else:
                    query = text(
                        """
                        SELECT DISTINCT p.name
                        FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        JOIN master.role_permissions rp ON r.id = rp.role_id
                        JOIN master.permissions p ON rp.permission_id = p.id
                        WHERE ur.user_id = :user_id
                          AND ur.context_type = :context_type
                          AND ur.context_id = :context_id
                          AND ur.status = 'active'
                          AND ur.deleted_at IS NULL
                          AND r.is_active = true
                          AND p.is_active = true
                        ORDER BY p.name
                    """
                    )
                    params = {
                        "user_id": user_id,
                        "context_type": context_type,
                        "context_id": context_id,
                    }

                result = await db.execute(query, params)

                permissions = [row[0] for row in result.fetchall()]

                logger.debug(
                    "🔍 Permissões buscadas do banco",
                    user_id=user_id,
                    context_type=context_type,
                    permissions_count=len(permissions),
                )

                return permissions

        except Exception as e:
            logger.error(f"❌ Erro ao buscar permissões do banco: {e}")
            return []

    async def has_permission(
        self,
        user_id: int,
        permission: str,
        context_type: str,
        context_id: Optional[int] = None,
    ) -> bool:
        """
        Verificação rápida se usuário tem permissão específica
        """
        try:
            # Buscar todas as permissões (usa cache)
            permissions = await self.get_user_permissions(
                user_id, context_type, context_id
            )

            has_perm = permission in permissions

            logger.debug(
                "🔐 Verificação de permissão",
                user_id=user_id,
                permission=permission,
                context_type=context_type,
                result=has_perm,
            )

            return has_perm

        except Exception as e:
            logger.error(
                f"❌ Erro na verificação de permissão",
                user_id=user_id,
                permission=permission,
                error=str(e),
            )
            return False

    async def has_any_permission(
        self,
        user_id: int,
        permissions: List[str],
        context_type: str,
        context_id: Optional[int] = None,
    ) -> bool:
        """Verificar se usuário tem QUALQUER uma das permissões"""
        try:
            user_permissions = await self.get_user_permissions(
                user_id, context_type, context_id
            )
            user_perm_set = set(user_permissions)
            required_perm_set = set(permissions)

            has_any = bool(user_perm_set & required_perm_set)

            logger.debug(
                "🔐 Verificação ANY permission",
                user_id=user_id,
                required_permissions=permissions,
                result=has_any,
            )

            return has_any

        except Exception as e:
            logger.error(f"❌ Erro na verificação ANY: {e}")
            return False

    async def has_all_permissions(
        self,
        user_id: int,
        permissions: List[str],
        context_type: str,
        context_id: Optional[int] = None,
    ) -> bool:
        """Verificar se usuário tem TODAS as permissões"""
        try:
            user_permissions = await self.get_user_permissions(
                user_id, context_type, context_id
            )
            user_perm_set = set(user_permissions)
            required_perm_set = set(permissions)

            has_all = required_perm_set.issubset(user_perm_set)

            logger.debug(
                "🔐 Verificação ALL permissions",
                user_id=user_id,
                required_permissions=permissions,
                result=has_all,
            )

            return has_all

        except Exception as e:
            logger.error(f"❌ Erro na verificação ALL: {e}")
            return False

    async def invalidate_user_cache(self, user_id: int):
        """Invalidar todo cache de permissões do usuário"""
        try:
            if not self.redis:
                return

            pattern = self._get_user_cache_pattern(user_id)
            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)
                logger.info(
                    "🗑️ Cache de usuário invalidado",
                    user_id=user_id,
                    keys_removed=len(keys),
                )
            else:
                logger.debug(
                    "🗑️ Nenhum cache encontrado para invalidar", user_id=user_id
                )

        except Exception as e:
            logger.error(f"❌ Erro ao invalidar cache: {e}")

    async def invalidate_context_cache(
        self, context_type: str, context_id: Optional[int] = None
    ):
        """Invalidar cache por contexto"""
        try:
            if not self.redis:
                return

            if context_id:
                pattern = f"permissions:user:*:ctx:{context_type}:{context_id}"
            else:
                pattern = f"permissions:user:*:ctx:{context_type}*"

            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)
                logger.info(
                    "🗑️ Cache de contexto invalidado",
                    context_type=context_type,
                    context_id=context_id,
                    keys_removed=len(keys),
                )

        except Exception as e:
            logger.error(f"❌ Erro ao invalidar cache de contexto: {e}")

    async def preload_user_permissions(
        self, user_id: int, contexts: List[Dict[str, Any]]
    ):
        """Pre-carregar permissões de múltiplos contextos para um usuário"""
        try:
            tasks = []
            for context in contexts:
                task = self.get_user_permissions(
                    user_id, context["context_type"], context.get("context_id")
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            logger.info(
                "🚀 Permissões pré-carregadas",
                user_id=user_id,
                contexts_count=len(contexts),
            )

        except Exception as e:
            logger.error(f"❌ Erro no pré-carregamento: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Estatísticas do cache de permissões"""
        try:
            if not self.redis:
                return {"status": "redis_unavailable"}

            # Contar chaves de permissões
            keys = await self.redis.keys("permissions:user:*")
            total_keys = len(keys)

            # Informações gerais do Redis
            info = await self.redis.info("memory")
            memory_used = info.get("used_memory_human", "unknown")

            # Estatísticas de TTL
            ttl_stats = {}
            if keys:
                sample_keys = keys[:10]  # Amostra de 10 chaves
                for key in sample_keys:
                    ttl = await self.redis.ttl(key)
                    if ttl > 0:
                        remaining_minutes = ttl // 60
                        ttl_stats[key] = f"{remaining_minutes}min"

            return {
                "status": "active",
                "total_cached_users": total_keys,
                "redis_memory_used": memory_used,
                "cache_ttl_minutes": self.cache_ttl // 60,
                "sample_ttls": ttl_stats,
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {"status": "error", "error": str(e)}

    async def clear_all_permission_cache(self):
        """Limpar todo cache de permissões (usar com cuidado)"""
        try:
            if not self.redis:
                return

            keys = await self.redis.keys("permissions:*")
            if keys:
                await self.redis.delete(*keys)
                logger.warning(
                    "🧹 TODO cache de permissões limpo", keys_removed=len(keys)
                )

        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}")


# Instância global do cache
permission_cache = PermissionCache()


async def init_permission_cache():
    """Inicializar cache de permissões na startup da aplicação"""
    await permission_cache.init_redis()


async def cleanup_permission_cache():
    """Limpar cache na shutdown da aplicação"""
    await permission_cache.close_redis()


# Funções utilitárias para uso direto
async def has_permission(
    user_id: int,
    permission: str,
    context_type: str = "establishment",
    context_id: Optional[int] = None,
) -> bool:
    """Função utilitária para verificação rápida de permissão"""
    return await permission_cache.has_permission(
        user_id, permission, context_type, context_id
    )


async def get_user_permissions(
    user_id: int, context_type: str = "establishment", context_id: Optional[int] = None
) -> List[str]:
    """Função utilitária para buscar permissões do usuário"""
    return await permission_cache.get_user_permissions(
        user_id, context_type, context_id
    )


async def invalidate_user_permissions(user_id: int):
    """Função utilitária para invalidar cache do usuário"""
    await permission_cache.invalidate_user_cache(user_id)
