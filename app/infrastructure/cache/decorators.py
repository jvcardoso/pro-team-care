import functools
import hashlib
from typing import Any, Callable, Optional

from app.infrastructure.cache.simplified_redis import (
    simplified_redis_client as redis_client,
)
from app.infrastructure.logging import logger


def generate_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate a unique cache key from function name and arguments"""
    # Create a string representation of all arguments
    args_str = str(args) + str(sorted(kwargs.items()))

    # Hash the arguments to create a consistent key
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]

    return f"cache:func:{func_name}:{args_hash}"


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    skip_cache: Optional[Callable] = None,
    invalidate_patterns: Optional[list] = None,
):
    """
    Cache decorator for async functions

    Args:
        ttl: Time to live in seconds (uses default from settings if None)
        key_prefix: Custom prefix for cache key
        skip_cache: Function that returns True if cache should be skipped
        invalidate_patterns: List of cache patterns to invalidate after function execution
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Check if we should skip cache
            if skip_cache and await skip_cache(*args, **kwargs):
                logger.debug(
                    f"Skipping cache for {func.__name__} due to skip_cache condition"
                )
                result = await func(*args, **kwargs)

                # Invalidate patterns if specified
                if invalidate_patterns:
                    for pattern in invalidate_patterns:
                        await redis_client.clear_pattern(pattern)

                return result

            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            if key_prefix:
                func_name = f"{key_prefix}:{func_name}"

            cache_key = generate_cache_key(func_name, *args, **kwargs)

            # Try to get from cache first
            cached_result = await redis_client.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Store result in cache using simplified API
            await redis_client.set(cache_key, result, ttl)

            # Invalidate patterns if specified
            if invalidate_patterns:
                for pattern in invalidate_patterns:
                    await redis_client.clear_pattern(pattern)

            return result

        # Add cache management methods to the decorated function
        wrapper.cache_key = lambda *args, **kwargs: generate_cache_key(
            (
                f"{key_prefix}:{func.__module__}.{func.__name__}"
                if key_prefix
                else f"{func.__module__}.{func.__name__}"
            ),
            *args,
            **kwargs,
        )
        wrapper.invalidate_cache = lambda *args, **kwargs: redis_client.delete(
            wrapper.cache_key(*args, **kwargs)
        )
        wrapper.cache_exists = lambda *args, **kwargs: redis_client.exists(
            wrapper.cache_key(*args, **kwargs)
        )

        return wrapper

    return decorator


def cache_invalidate(*patterns: str):
    """
    Decorator to invalidate cache patterns after function execution

    Args:
        patterns: Cache patterns to invalidate
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            # Invalidate cache patterns
            for pattern in patterns:
                cleared_count = await redis_client.clear_pattern(pattern)
                logger.debug(
                    f"Invalidated {cleared_count} cache entries for pattern: {pattern}"
                )

            return result

        return wrapper

    return decorator


class CacheManager:
    """Centralized cache management"""

    @staticmethod
    async def warm_up_cache(cache_functions: list):
        """Warm up cache by executing specified functions"""
        logger.info("Starting cache warm-up process")

        for func_info in cache_functions:
            try:
                func = func_info["function"]
                args = func_info.get("args", ())
                kwargs = func_info.get("kwargs", {})

                await func(*args, **kwargs)
                logger.debug(f"Cache warmed up for: {func.__name__}")

            except Exception as e:
                logger.error(f"Cache warm-up failed for {func.__name__}: {e}")

        logger.info("Cache warm-up completed")

    @staticmethod
    async def cache_health_check() -> dict:
        """Check cache system health"""
        try:
            is_connected = await redis_client.is_connected()
            info = await redis_client.get_info()

            return {
                "status": "healthy" if is_connected else "unhealthy",
                "connected": is_connected,
                "redis_info": info,
            }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"status": "unhealthy", "connected": False, "error": str(e)}

    @staticmethod
    async def get_cache_stats() -> dict:
        """Get cache statistics"""
        try:
            info = await redis_client.get_info()

            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total_requests = hits + misses

            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "hits": hits,
                "misses": misses,
                "hit_rate_percentage": round(hit_rate, 2),
                "total_requests": total_requests,
                "memory_used": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


# Export cache manager instance
cache_manager = CacheManager()
