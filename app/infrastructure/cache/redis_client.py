import json
import pickle
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.infrastructure.logging import logger
from config.settings import settings


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis server"""
        try:
            redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
            if settings.redis_password:
                redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
                
            self.redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle serialization manually
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=20
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, using mock for testing: {e}")
            # Use mock redis for testing when real Redis is not available
            from app.infrastructure.cache.mock_redis import MockRedis
            self.redis = MockRedis()
            
    async def disconnect(self):
        """Disconnect from Redis server"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis connection closed")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception:
            pass
        return False
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set a key-value pair with optional TTL"""
        if not self.redis:
            logger.warning("Redis not connected, cache set operation skipped")
            return False
            
        try:
            if serialize:
                # Use pickle for complex objects, JSON for simple types
                if isinstance(value, (str, int, float, bool, list, dict)):
                    serialized_value = json.dumps(value).encode('utf-8')
                    key = f"json:{key}"
                else:
                    serialized_value = pickle.dumps(value)
                    key = f"pickle:{key}"
            else:
                serialized_value = value
                
            ttl = ttl or settings.cache_ttl
            await self.redis.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def get(self, key: str, serialize: bool = True) -> Optional[Any]:
        """Get a value by key"""
        if not self.redis:
            logger.warning("Redis not connected, cache get operation skipped")
            return None
            
        try:
            # Try both JSON and pickle formats
            json_key = f"json:{key}"
            pickle_key = f"pickle:{key}"
            
            # Try JSON format first
            value = await self.redis.get(json_key)
            if value:
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, AttributeError):
                    pass
                    
            # Try pickle format
            value = await self.redis.get(pickle_key)
            if value:
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, AttributeError):
                    pass
                    
            # Try direct key (for non-serialized data)
            if not serialize:
                value = await self.redis.get(key)
                return value.decode('utf-8') if value else None
                
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        if not self.redis:
            return False
            
        try:
            # Delete all possible formats
            keys_to_delete = [key, f"json:{key}", f"pickle:{key}"]
            deleted_count = await self.redis.delete(*keys_to_delete)
            logger.debug(f"Cache delete: {key} (deleted {deleted_count} keys)")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
            
        try:
            # Check all possible formats
            keys_to_check = [key, f"json:{key}", f"pickle:{key}"]
            exists_count = await self.redis.exists(*keys_to_check)
            return exists_count > 0
            
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for a key"""
        if not self.redis:
            return False
            
        try:
            # Set expiration for all possible formats
            keys_to_expire = [key, f"json:{key}", f"pickle:{key}"]
            for k in keys_to_expire:
                if await self.redis.exists(k):
                    await self.redis.expire(k, ttl)
                    
            return True
            
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching a pattern"""
        if not self.redis:
            return 0
            
        try:
            # Find keys matching pattern in all formats
            patterns = [pattern, f"json:{pattern}", f"pickle:{pattern}"]
            deleted_count = 0
            
            for p in patterns:
                keys = []
                async for key in self.redis.scan_iter(match=p):
                    keys.append(key)
                    
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                    
            logger.info(f"Cache clear pattern {pattern}: {deleted_count} keys deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Redis clear pattern error for {pattern}: {e}")
            return 0
    
    async def flush_db(self) -> bool:
        """Clear all keys in current database"""
        if not self.redis:
            return False
            
        try:
            await self.redis.flushdb()
            logger.info("Redis database flushed")
            return True
            
        except Exception as e:
            logger.error(f"Redis flush error: {e}")
            return False
    
    async def get_info(self) -> dict:
        """Get Redis server information"""
        if not self.redis:
            return {}
            
        try:
            info = await self.redis.info()
            return {
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
            
        except Exception as e:
            logger.error(f"Redis info error: {e}")
            return {}


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client