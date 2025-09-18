from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    ⚠️ MIDDLEWARE SIMPLIFICADO - NÃO ADICIONAR HEADERS COMPLEXOS!

    Este middleware foi INTENCIONALMENTE simplificado.
    LEIA: SECURITY_SIMPLE.md antes de modificar.

    ❌ NÃO ADICIONE:
    - CSP (Content-Security-Policy)
    - HSTS (Strict-Transport-Security)
    - Permissions-Policy
    - Referrer-Policy restritivo
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # ⚠️ APENAS HEADERS ESSENCIAIS - NÃO ADICIONE MAIS!
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Menos restritivo que DENY

        return response
