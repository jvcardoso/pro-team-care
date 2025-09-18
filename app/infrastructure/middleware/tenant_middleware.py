"""
Middleware Multi-Tenant
Configura automaticamente o contexto da empresa baseado no JWT do usuário
"""

import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.auth import decode_token
from app.infrastructure.database import async_session
from app.infrastructure.services.tenant_context_service import get_tenant_context

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware para configurar contexto multi-tenant automaticamente"""

    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next):
        """Processar requisição configurando contexto multi-tenant"""

        # Verificar se o path deve ser excluído
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Obter token de autorização
        authorization = request.headers.get("Authorization")

        if not authorization or not authorization.startswith("Bearer "):
            # Para endpoints públicos, prosseguir sem contexto
            return await call_next(request)

        try:
            # Extrair e decodificar token
            token = authorization.split(" ")[1]
            payload = decode_token(token)

            if not payload:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token inválido"},
                )

            user_id = payload.get("sub")
            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token sem user ID"},
                )

            # Obter company_id do usuário
            tenant_service = get_tenant_context()

            async with async_session() as session:
                company_id = await tenant_service.get_user_company_id(
                    session, int(user_id)
                )

                if company_id is None:
                    logger.warning(f"Usuário {user_id} não possui empresa associada")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Usuário sem empresa associada"},
                    )

                # Configurar contexto multi-tenant
                tenant_service.set_company_id(company_id)

                # Adicionar company_id ao request para uso posterior
                request.state.company_id = company_id
                request.state.user_id = int(user_id)

                logger.debug(
                    f"Contexto multi-tenant configurado - User: {user_id}, Company: {company_id}"
                )

        except Exception as e:
            logger.error(f"Erro no middleware multi-tenant: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Erro interno do servidor"},
            )

        # Prosseguir com a requisição
        response = await call_next(request)

        # Limpar contexto após a requisição
        try:
            tenant_service = get_tenant_context()
            tenant_service.set_company_id(None)
        except Exception as e:
            logger.error(f"Erro ao limpar contexto multi-tenant: {e}")

        return response


def get_company_id_from_request(request: Request) -> int:
    """Obter company_id da requisição atual"""
    if not hasattr(request.state, "company_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contexto multi-tenant não configurado",
        )
    return request.state.company_id


def get_user_id_from_request(request: Request) -> int:
    """Obter user_id da requisição atual"""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado"
        )
    return request.state.user_id


async def get_tenant_session(request: Request) -> AsyncSession:
    """Obter sessão de banco configurada com contexto multi-tenant"""
    company_id = get_company_id_from_request(request)
    tenant_service = get_tenant_context()

    session = async_session()
    await tenant_service.set_database_context(session, company_id)

    return session
