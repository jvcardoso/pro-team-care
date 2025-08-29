"""
Simplified Redis client with cleaner serialization logic and improved error handling
"""
import json
import pickle
import asyncio
from typing import Any, Optional, Dict
from enum import Enum
import redis.asyncio as redis
from app.infrastructure.logging import logger
from config.settings import settings


class SerializationMethod(Enum):
    """Serialization methods for cache values"""
    JSON = "json"
    PICKLE = "pickle"
    RAW = "raw"


class SimplifiedRedisClient:
    """Simplified Redis client with cleaner logic and improved error handling"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._is_mock = False
        self._connection_retries = 3
        self._retry_delay = 1.0
    
    async def connect(self):
        """Connect to Redis server with retry logic and fallback to mock"""
        last_error = None
        
        for attempt in range(self._connection_retries):
            try:
                redis_url = self._build_redis_url()
                self.redis = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    max_connections=10
                )
                
                await self.redis.ping()
                logger.info(f"Redis connection established on attempt {attempt + 1}")
                self._is_mock = False
                return
                
            except (redis.ConnectionError, redis.TimeoutError, OSError) as e:
                last_error = e
                if attempt < self._connection_retries - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}. Retrying in {self._retry_delay}s...")
                    await asyncio.sleep(self._retry_delay)
                    continue
                else:
                    logger.error(f"Redis connection failed after {self._connection_retries} attempts: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error during Redis connection: {e}")
                break
        
        logger.warning(f"Redis unavailable, using mock fallback. Last error: {last_error}")
        from app.infrastructure.cache.mock_redis import MockRedis
        self.redis = MockRedis()
        self._is_mock = True
    
    def _build_redis_url(self) -> str:
        """Build Redis connection URL"""
        if settings.redis_password:
            return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    
    async def disconnect(self):
        """Disconnect from Redis with proper error handling"""
        if self.redis and not self._is_mock:
            try:
                await self.redis.close()
                logger.info("Redis connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        self.redis = None
    
    async def is_connected(self) -> bool:
        """Check Redis connection with detailed error logging"""
        try:
            if self.redis:
                if self._is_mock:
                    return True
                await self.redis.ping()
                return True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.debug(f"Redis connection check failed: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error during Redis ping: {e}")
        return False
    
    def _serialize_value(self, value: Any) -> tuple[bytes, SerializationMethod]:
        """Serialize value using the best method with improved error handling"""
        # Try JSON first (most compatible)
        try:
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                return json.dumps(value, default=str).encode('utf-8'), SerializationMethod.JSON
        except (TypeError, ValueError) as e:
            logger.debug(f"JSON serialization failed for {type(value)}: {e}")
        
        # Fallback to pickle for complex objects
        try:
            return pickle.dumps(value), SerializationMethod.PICKLE
        except (pickle.PickleError, TypeError) as e:
            logger.warning(f"Pickle serialization failed for {type(value)}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during pickle serialization: {e}")
        
        # Last resort: convert to string
        try:
            return str(value).encode('utf-8'), SerializationMethod.RAW
        except Exception as e:
            logger.error(f"Failed to serialize value as string: {e}")
            raise ValueError(f"Unable to serialize value of type {type(value)}")from e
    
    def _deserialize_value(self, data: bytes, method: SerializationMethod) -> Any:
        """Deserialize value based on method with improved error handling"""
        try:
            if method == SerializationMethod.JSON:
                return json.loads(data.decode('utf-8'))
            elif method == SerializationMethod.PICKLE:
                return pickle.loads(data)
            else:  # RAW
                return data.decode('utf-8')
        except json.JSONDecodeError as e:
            logger.warning(f"JSON deserialization failed: {e}")
            return None
        except pickle.PickleError as e:
            logger.warning(f"Pickle deserialization failed: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.warning(f"Unicode decode error during deserialization: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected deserialization error for method {method}: {e}")
            return None
    
    def _make_key(self, key: str, method: SerializationMethod) -> str:
        """Create prefixed key based on serialization method"""
        return f"{method.value}:{key}"
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value with automatic serialization and error handling"""
        if not self.redis:
            logger.warning("Redis not available for set operation")
            return False
        
        try:
            serialized_value, method = self._serialize_value(value)
            prefixed_key = self._make_key(key, method)
            
            ttl = ttl or settings.cache_ttl
            await self.redis.setex(prefixed_key, ttl, serialized_value)
            
            logger.debug(f"Cache set: {key} ({method.value}, {len(serialized_value)} bytes, TTL: {ttl}s)")
            return True
            
        except ValueError as e:
            logger.error(f"Serialization error for key {key}: {e}")
            return False
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection error during set for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache set for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value with automatic deserialization and error handling"""
        if not self.redis:
            logger.warning("Redis not available for get operation")
            return None
        
        # Try all serialization methods in order of preference
        methods = [SerializationMethod.JSON, SerializationMethod.PICKLE, SerializationMethod.RAW]
        
        for method in methods:
            try:
                prefixed_key = self._make_key(key, method)
                data = await self.redis.get(prefixed_key)
                
                if data:
                    result = self._deserialize_value(data, method)
                    if result is not None:
                        logger.debug(f"Cache hit: {key} ({method.value})")
                        return result
                        
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Redis connection error during get for key {key}: {e}")
                return None
            except Exception as e:
                logger.debug(f"Cache get attempt failed for {key} with {method.value}: {e}")
                continue
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from all possible formats with error handling"""
        if not self.redis:
            logger.warning("Redis not available for delete operation")
            return False
        
        try:
            keys_to_delete = [
                self._make_key(key, method) 
                for method in SerializationMethod
            ]
            
            deleted = await self.redis.delete(*keys_to_delete)
            logger.debug(f"Cache delete: {key} ({deleted} keys removed)")
            return deleted > 0
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection error during delete for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache delete for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any format with error handling"""
        if not self.redis:
            logger.debug("Redis not available for exists check")
            return False
        
        try:
            keys_to_check = [
                self._make_key(key, method) 
                for method in SerializationMethod
            ]
            
            exists_count = await self.redis.exists(*keys_to_check)
            return exists_count > 0
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection error during exists check for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during cache exists check for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern with error handling"""
        if not self.redis:
            logger.warning("Redis not available for clear pattern operation")
            return 0
        
        try:
            deleted = 0
            for method in SerializationMethod:
                prefixed_pattern = self._make_key(pattern, method)
                
                keys = []
                try:
                    async for key in self.redis.scan_iter(match=prefixed_pattern):
                        keys.append(key)
                except Exception as e:
                    logger.warning(f"Error scanning for pattern {prefixed_pattern}: {e}")
                    continue
                
                if keys:
                    try:
                        deleted += await self.redis.delete(*keys)
                    except Exception as e:
                        logger.error(f"Error deleting keys for pattern {prefixed_pattern}: {e}")
                        continue
            
            logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
            return deleted
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection error during clear pattern for {pattern}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error during clear pattern for {pattern}: {e}")
            return 0
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis info with comprehensive error handling"""
        if not self.redis:
            return {"connected": False, "error": "Redis client not initialized"}
        
        try:
            if self._is_mock:
                mock_info = await self.redis.info()
                return {
                    "connected": True,
                    "is_mock": True,
                    **mock_info
                }
            
            info = await self.redis.info()
            return {
                "connected": True,
                "is_mock": False,
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redis connection error during info request: {e}")
            return {"connected": False, "error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error during Redis info request: {e}")
            return {"connected": False, "error": f"Unexpected error: {str(e)}"}


# Global instance
simplified_redis_client = SimplifiedRedisClient()


# Compatibility function
async def get_simplified_redis() -> SimplifiedRedisClient:
    """Get the simplified Redis client instance"""
    return simplified_redis_client