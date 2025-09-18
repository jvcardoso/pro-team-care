import os

# Configure structured logging
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from structlog import get_logger

from app.presentation.api.v1.api import api_router
from config.settings import settings

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = get_logger()

app = FastAPI(
    title="Pro Team Care API",
    description="""
    ## 🚀 Sistema de Gestão de Equipe Profissional

    API completa para gestão de empresas, equipes e relacionamentos profissionais.

    ### 🏗️ Arquitetura
    - **Clean Architecture** com separação de responsabilidades
    - **FastAPI** com validação automática via Pydantic
    - **PostgreSQL** para persistência com SQLAlchemy assíncrono
    - **JWT Authentication** com segurança bcrypt
    - **Rate Limiting** para proteção contra abuse

    ### 🔐 Segurança
    - Autenticação JWT obrigatória em endpoints protegidos
    - Rate limiting (5 tentativas/min para login)
    - Security headers (CORS, XSS protection, etc.)
    - Validação rigorosa de entrada de dados

    ### 📊 Funcionalidades Principais
    - **Companies**: CRUD completo de empresas com validação de CNPJ
    - **CNPJ Lookup**: Integração com ReceitaWS para enriquecimento
    - **Authentication**: Sistema completo de login/registro
    - **Geolocation**: Enriquecimento automático de endereços

    ### 🔗 Links Úteis
    - [Documentação Interativa](/docs)
    - [Documentação ReDoc](/redoc)
    - [Health Check](/api/v1/health)
    - [Métricas Prometheus](/metrics)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Autenticação e autorização de usuários",
        },
        {
            "name": "Companies",
            "description": "Gestão completa de empresas e seus dados",
        },
        {
            "name": "CNPJ Lookup",
            "description": "Consulta e enriquecimento de dados via CNPJ",
        },
        {
            "name": "Hierarchical Users",
            "description": "Sistema hierárquico de usuários com controle de acesso avançado",
        },
        {
            "name": "Secure Sessions",
            "description": "Sistema de sessões seguras com troca de perfil e personificação",
        },
        {
            "name": "Development",
            "description": "Endpoints para desenvolvimento e debugging",
        },
        {"name": "Health", "description": "Monitoramento e status do sistema"},
    ],
)

from app.infrastructure.monitoring.middleware import setup_monitoring_middleware
from app.infrastructure.rate_limiting import setup_rate_limiting

# Security middleware
from app.infrastructure.security_middleware import SecurityHeadersMiddleware


# CORS configuration with validation - MUST be first
def get_cors_origins():
    """Get and validate CORS origins"""
    origins = settings.cors_origins_list
    logger.info("CORS origins configured", origins=origins)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],  # More restrictive
)

app.add_middleware(SecurityHeadersMiddleware)

# Setup rate limiting
rate_limiter = setup_rate_limiting(app)

# Setup monitoring middleware
setup_monitoring_middleware(app)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts.split(","),
)

# Exception handlers
from app.infrastructure.exceptions import (
    BusinessException,
    NotFoundException,
    ValidationException,
    business_exception_handler,
    general_exception_handler,
    not_found_exception_handler,
    validation_exception_handler,
)

app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Manual OpenAPI endpoint (bypasses problematic decorators)
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Serve basic OpenAPI schema"""
    try:
        # Return a minimal schema to make docs work
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Pro Team Care API",
                "version": "1.0.0",
                "description": "API completa para gestão de empresas, equipes e relacionamentos profissionais.",
            },
            "paths": {
                "/api/v1/health": {
                    "get": {
                        "summary": "Health Check",
                        "responses": {"200": {"description": "API is healthy"}},
                    }
                },
                "/docs": {
                    "get": {
                        "summary": "API Documentation",
                        "responses": {
                            "200": {"description": "Swagger UI documentation"}
                        },
                    }
                },
            },
        }
    except Exception as e:
        # Fallback in case of any error
        return {"error": "Schema generation failed", "message": str(e)}


# Static files configuration for frontend
frontend_dist_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)


# Specific routes (must come before catch-all)
@app.get("/simple_db_admin.html")
async def serve_db_admin():
    """Serve the database admin HTML page"""
    db_admin_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "simple_db_admin.html"
    )
    if os.path.exists(db_admin_path):
        return FileResponse(db_admin_path)
    raise HTTPException(status_code=404, detail="Database admin page not found")


if os.path.exists(frontend_dist_path):
    # Serve static assets (CSS, JS, images, etc.)
    app.mount("/static", StaticFiles(directory=frontend_dist_path), name="static")

    # Serve frontend index.html for SPA routing
    @app.get("/")
    @app.get("/{path:path}")
    async def serve_frontend(path: str = ""):
        """Serve React frontend for all non-API routes"""
        # Skip API routes
        if (
            path.startswith("api/")
            or path.startswith("docs")
            or path.startswith("redoc")
            or path.startswith("openapi.json")
        ):
            raise HTTPException(status_code=404, detail="Not found")

        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Frontend not built yet. Run: cd frontend && npm run build"}

else:

    @app.get("/")
    async def root():
        """Root endpoint when frontend is not available"""
        return {
            "message": "Pro Team Care API",
            "version": "1.0.0",
            "docs": "/docs",
            "frontend_status": "Not built. Run: cd frontend && npm run build",
        }


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Pro Team Care API", version="1.0.0")

    # Initialize Redis connection
    from app.infrastructure.cache.simplified_redis import simplified_redis_client

    await simplified_redis_client.connect()

    # Start performance monitoring
    from app.infrastructure.monitoring.metrics import performance_metrics

    await performance_metrics.start_system_monitoring(interval=30)

    logger.info("All systems initialized")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Pro Team Care API")

    # Stop performance monitoring
    from app.infrastructure.monitoring.metrics import performance_metrics

    await performance_metrics.stop_system_monitoring()

    # Close Redis connection
    from app.infrastructure.cache.simplified_redis import simplified_redis_client

    await simplified_redis_client.disconnect()

    logger.info("All systems shut down gracefully")


# Basic health endpoint (legacy - now handled by health router)
