from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# ⚠️ RATE LIMITER SIMPLIFICADO - NÃO COMPLICAR!
# LEIA: SECURITY_SIMPLE.md antes de alterar
# ❌ NÃO ADICIONE: Redis, storage inteligente, configurações complexas
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # ⚠️ NÃO MUDAR - sempre memória, sem dependencies
)


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Too many requests.",
            "retry_after": exc.retry_after,
        },
    )


def setup_rate_limiting(app):
    """Configure rate limiting for FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    return limiter
