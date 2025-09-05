"""
Metrics and monitoring endpoints
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Response, Request
from fastapi.responses import PlainTextResponse

from app.infrastructure.monitoring.metrics import performance_metrics
from app.infrastructure.rate_limiting import limiter
from app.infrastructure.logging import logger

router = APIRouter(tags=["Monitoring"])


@router.get("/metrics")
async def prometheus_metrics() -> PlainTextResponse:
    """Prometheus metrics endpoint"""
    try:
        metrics_data = performance_metrics.export_prometheus_metrics()
        return PlainTextResponse(
            content=metrics_data.decode('utf-8'),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Failed to export Prometheus metrics: {e}")
        return PlainTextResponse(
            content=f"# Error exporting metrics: {e}",
            media_type="text/plain"
        )


@router.get("/metrics/summary")
@limiter.limit("10/minute")
async def metrics_summary(request: Request) -> Dict[str, Any]:
    """Get metrics summary in JSON format"""
    try:
        summary = performance_metrics.get_metrics_summary()
        summary["timestamp_iso"] = datetime.utcnow().isoformat()
        
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp_iso": datetime.utcnow().isoformat()
        }


@router.get("/metrics/health")
@limiter.limit("20/minute")
async def metrics_health_check(request: Request) -> Dict[str, Any]:
    """Health check for metrics system"""
    try:
        # Test basic metrics functionality
        test_summary = performance_metrics.get_metrics_summary()
        
        return {
            "status": "healthy",
            "metrics_system": "operational",
            "prometheus_export": "available",
            "system_monitoring": "active" if performance_metrics._system_monitor_task else "inactive",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/metrics/test")
@limiter.limit("5/minute")  
async def test_metrics(request: Request) -> Dict[str, Any]:
    """Test endpoint to generate sample metrics"""
    try:
        # Generate some test metrics
        performance_metrics.record_http_request("GET", "/test", 200, 0.1)
        performance_metrics.record_http_request("POST", "/test", 201, 0.2)
        performance_metrics.record_cache_operation("get", "hit")
        performance_metrics.record_cache_operation("get", "miss")
        performance_metrics.record_auth_attempt("success")
        performance_metrics.update_active_users(10)
        
        await performance_metrics.update_system_metrics()
        
        logger.info("Generated test metrics")
        
        return {
            "status": "success",
            "message": "Test metrics generated",
            "metrics_generated": [
                "http_requests_total",
                "http_request_duration_seconds", 
                "cache_operations_total",
                "auth_attempts_total",
                "active_users",
                "system_cpu_usage_percent",
                "system_memory_usage_percent"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test metrics: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }