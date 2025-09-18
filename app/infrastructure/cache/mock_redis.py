"""Mock Redis client for testing when Redis is not available"""

import json
import pickle
from typing import Any, Dict, Optional

from app.infrastructure.logging import logger


class MockRedis:
    """Mock Redis implementation for testing"""

    def __init__(self):
        self._data: Dict[str, bytes] = {}
        self._expiry: Dict[str, float] = {}

    async def ping(self) -> bool:
        return True

    async def close(self):
        pass

    async def setex(self, key: str, ttl: int, value: bytes) -> bool:
        self._data[key] = value
        # Simple TTL mock - not time-based for testing
        self._expiry[key] = ttl
        return True

    async def get(self, key: str) -> Optional[bytes]:
        return self._data.get(key)

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                self._expiry.pop(key, None)
                deleted += 1
        return deleted

    async def exists(self, *keys: str) -> int:
        return sum(1 for key in keys if key in self._data)

    async def expire(self, key: str, ttl: int) -> bool:
        if key in self._data:
            self._expiry[key] = ttl
            return True
        return False

    async def scan_iter(self, match: str = "*"):
        """Simple pattern matching for testing"""
        import fnmatch

        for key in self._data:
            if fnmatch.fnmatch(key, match):
                yield key

    async def flushdb(self) -> bool:
        self._data.clear()
        self._expiry.clear()
        return True

    async def info(self) -> Dict[str, Any]:
        return {
            "redis_version": "mock-1.0.0",
            "used_memory_human": "1K",
            "connected_clients": 1,
            "total_commands_processed": len(self._data),
            "keyspace_hits": 0,
            "keyspace_misses": 0,
            "used_memory": 1024,
        }


class MockRedisClient:
    """Mock version of RedisClient for testing"""

    def __init__(self):
        self.redis = MockRedis()
        self._connected = True

    async def connect(self):
        self._connected = True
        logger.info("Mock Redis connection established")

    async def disconnect(self):
        self._connected = False
        logger.info("Mock Redis connection closed")

    async def is_connected(self) -> bool:
        return self._connected

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, serialize: bool = True
    ) -> bool:
        if not self._connected:
            return False

        try:
            if serialize:
                if isinstance(value, (str, int, float, bool, list, dict)):
                    serialized_value = json.dumps(value).encode("utf-8")
                    key = f"json:{key}"
                else:
                    serialized_value = pickle.dumps(value)
                    key = f"pickle:{key}"
            else:
                serialized_value = (
                    value if isinstance(value, bytes) else str(value).encode()
                )

            await self.redis.setex(key, ttl or 300, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Mock Redis set error: {e}")
            return False

    async def get(self, key: str, serialize: bool = True) -> Optional[Any]:
        if not self._connected:
            return None

        try:
            # Try both JSON and pickle formats
            for prefix in ["json:", "pickle:", ""]:
                test_key = f"{prefix}{key}" if prefix else key
                value = await self.redis.get(test_key)

                if value:
                    if prefix == "json:":
                        return json.loads(value.decode("utf-8"))
                    elif prefix == "pickle:":
                        return pickle.loads(value)
                    else:
                        return value.decode("utf-8") if serialize else value

            return None
        except Exception as e:
            logger.error(f"Mock Redis get error: {e}")
            return None

    async def delete(self, key: str) -> bool:
        if not self._connected:
            return False

        keys_to_delete = [key, f"json:{key}", f"pickle:{key}"]
        deleted_count = await self.redis.delete(*keys_to_delete)
        return deleted_count > 0

    async def exists(self, key: str) -> bool:
        if not self._connected:
            return False

        keys_to_check = [key, f"json:{key}", f"pickle:{key}"]
        exists_count = await self.redis.exists(*keys_to_check)
        return exists_count > 0

    async def expire(self, key: str, ttl: int) -> bool:
        if not self._connected:
            return False

        keys_to_expire = [key, f"json:{key}", f"pickle:{key}"]
        for k in keys_to_expire:
            if await self.redis.exists(k):
                await self.redis.expire(k, ttl)
        return True

    async def clear_pattern(self, pattern: str) -> int:
        if not self._connected:
            return 0

        patterns = [pattern, f"json:{pattern}", f"pickle:{pattern}"]
        deleted_count = 0

        for p in patterns:
            keys = []
            async for key in self.redis.scan_iter(match=p):
                keys.append(key)

            if keys:
                deleted_count += await self.redis.delete(*keys)

        return deleted_count

    async def flush_db(self) -> bool:
        if not self._connected:
            return False

        await self.redis.flushdb()
        return True

    async def get_info(self) -> dict:
        if not self._connected:
            return {}

        return await self.redis.info()
