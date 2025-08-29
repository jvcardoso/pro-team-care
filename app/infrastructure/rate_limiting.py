from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from slowapi.middleware import SlowAPIMiddleware
from config.settings import settings


def get_rate_limit_storage_uri() -> str:
    """Get storage URI for rate limiting - Redis in production, memory in test/dev"""
    import os
    
    # Force memory storage in test environments
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("ENV_FILE") == ".env.test":
        return "memory://"
    
    try:
        # Try Redis for production
        import redis
        # Test Redis connection
        if settings.redis_password:
            test_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        else:
            test_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        
        # Quick connection test
        r = redis.from_url(test_url)
        r.ping()  # This will raise exception if Redis not available
        return test_url
    except Exception:
        # Fallback to memory storage if Redis not available
        return "memory://"


# Initialize rate limiter with intelligent storage selection
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_rate_limit_storage_uri(),
)


def setup_rate_limiting(app):
    """Configure rate limiting for FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    return limiter