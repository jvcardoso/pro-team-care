from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from structlog import get_logger

from config.settings import settings
from app.presentation.api.v1.api import api_router

# Configure structured logging
import structlog
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = get_logger()

app = FastAPI(
    title="Pro Team Care API",
    description="API para sistema de gestão de equipe profissional",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Security middleware
from app.infrastructure.security_middleware import SecurityHeadersMiddleware
from app.infrastructure.rate_limiting import setup_rate_limiting
from app.infrastructure.monitoring.middleware import setup_monitoring_middleware

app.add_middleware(SecurityHeadersMiddleware)

# Setup rate limiting
rate_limiter = setup_rate_limiting(app)

# Setup monitoring middleware
setup_monitoring_middleware(app)

# CORS configuration with validation
def get_cors_origins():
    """Get and validate CORS origins"""
    origins = [origin.strip() for origin in settings.allowed_origins.split(",")]
    # Filter out empty strings
    origins = [origin for origin in origins if origin]
    logger.info("CORS origins configured", origins=origins)
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # More restrictive
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts.split(","),
)

# Exception handlers
from app.infrastructure.exceptions import (
    BusinessException, ValidationException, NotFoundException,
    business_exception_handler, validation_exception_handler,
    not_found_exception_handler, general_exception_handler
)

app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(NotFoundException, not_found_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

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