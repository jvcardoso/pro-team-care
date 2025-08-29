"""
Monitoring middleware for automatic performance tracking
"""
import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.monitoring.metrics import performance_metrics
from app.infrastructure.logging import logger


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic HTTP request monitoring"""
    
    def __init__(self, app, collect_detailed_metrics: bool = True):
        super().__init__(app)
        self.collect_detailed_metrics = collect_detailed_metrics
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip monitoring for certain paths
        if self._should_skip_monitoring(request.url.path):
            return await call_next(request)
        
        start_time = time.time()
        method = request.method
        path = self._normalize_path(request.url.path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            performance_metrics.record_http_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 1.0:  # Requests slower than 1 second
                logger.warning(
                    "Slow request detected",
                    method=method,
                    path=path,
                    duration=duration,
                    status_code=status_code
                )
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            performance_metrics.record_http_request(
                method=method,
                endpoint=path,
                status_code=500,
                duration=duration
            )
            
            performance_metrics.record_error(
                error_type=type(e).__name__,
                module="http_middleware"
            )
            
            logger.error(
                "Request failed with exception",
                method=method,
                path=path,
                duration=duration,
                error=str(e)
            )
            
            raise
    
    def _should_skip_monitoring(self, path: str) -> bool:
        """Check if path should be skipped from monitoring"""
        skip_paths = [
            "/metrics",  # Prometheus metrics endpoint
            "/health",   # Health checks
            "/docs",     # API documentation
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics to avoid high cardinality"""
        # Replace IDs with placeholder
        import re
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace UUIDs
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 
            '/{uuid}', 
            path
        )
        
        return path


class DatabaseMonitoringMixin:
    """Mixin for automatic database query monitoring"""
    
    async def execute_with_monitoring(self, query, params=None, operation="query", table="unknown"):
        """Execute database query with monitoring"""
        async with performance_metrics.track_db_query(operation, table):
            # This would be implemented by the specific database client
            # For now, it's a placeholder for the pattern
            pass


def setup_monitoring_middleware(app):
    """Setup monitoring middleware on FastAPI app"""
    app.add_middleware(
        PerformanceMonitoringMiddleware,
        collect_detailed_metrics=True
    )
    logger.info("Performance monitoring middleware enabled")