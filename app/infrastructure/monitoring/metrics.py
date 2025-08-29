"""
Performance monitoring and metrics collection
"""
import time
import psutil
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from functools import wraps
import asyncio
from contextlib import asynccontextmanager

from app.infrastructure.logging import logger


class PerformanceMetrics:
    """Centralized performance metrics collection"""
    
    def __init__(self):
        # Create custom registry for better control
        self.registry = CollectorRegistry()
        
        # HTTP Request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_errors_total = Counter(
            'db_errors_total',
            'Total database errors',
            ['error_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage',
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_memory_available = Gauge(
            'system_memory_available_bytes',
            'Available system memory in bytes',
            registry=self.registry
        )
        
        # Application metrics
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.auth_attempts_total = Counter(
            'auth_attempts_total',
            'Total authentication attempts',
            ['result'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total application errors',
            ['error_type', 'module'],
            registry=self.registry
        )
        
        # Performance tracking
        self._request_start_times = {}
        self._system_monitor_task = None
        
        logger.info("Performance metrics initialized")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        self.http_request_duration.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query metrics"""
        self.db_query_duration.labels(
            operation=operation, 
            table=table
        ).observe(duration)
    
    def record_db_error(self, error_type: str):
        """Record database error"""
        self.db_errors_total.labels(error_type=error_type).inc()
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation (hit/miss/set/delete)"""
        self.cache_operations_total.labels(
            operation=operation,
            result=result
        ).inc()
    
    def update_cache_hit_rate(self, hit_rate: float):
        """Update cache hit rate"""
        self.cache_hit_rate.set(hit_rate)
    
    def record_auth_attempt(self, result: str):
        """Record authentication attempt"""
        self.auth_attempts_total.labels(result=result).inc()
    
    def record_error(self, error_type: str, module: str):
        """Record application error"""
        self.errors_total.labels(
            error_type=error_type,
            module=module
        ).inc()
    
    def update_active_users(self, count: int):
        """Update active users count"""
        self.active_users.set(count)
    
    def update_db_connections(self, count: int):
        """Update active database connections"""
        self.db_connections_active.set(count)
    
    async def update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            self.system_memory_available.set(memory.available)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    @asynccontextmanager
    async def track_request_duration(self, method: str, endpoint: str):
        """Context manager to track HTTP request duration"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            # Note: status_code will be recorded separately
            logger.debug(f"Request {method} {endpoint} took {duration:.3f}s")
    
    @asynccontextmanager
    async def track_db_query(self, operation: str, table: str = "unknown"):
        """Context manager to track database query duration"""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            self.record_db_error(type(e).__name__)
            raise
        finally:
            duration = time.time() - start_time
            self.record_db_query(operation, table, duration)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        try:
            # System info
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            return {
                "timestamp": time.time(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / 1024 / 1024,
                    "memory_used_mb": memory.used / 1024 / 1024
                },
                "metrics_available": True
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": str(e), "metrics_available": False}
    
    def export_prometheus_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    async def start_system_monitoring(self, interval: int = 30):
        """Start background system monitoring"""
        if self._system_monitor_task:
            return
        
        async def monitor_loop():
            while True:
                try:
                    await self.update_system_metrics()
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    await asyncio.sleep(interval)
        
        self._system_monitor_task = asyncio.create_task(monitor_loop())
        logger.info(f"Started system monitoring with {interval}s interval")
    
    async def stop_system_monitoring(self):
        """Stop background system monitoring"""
        if self._system_monitor_task:
            self._system_monitor_task.cancel()
            try:
                await self._system_monitor_task
            except asyncio.CancelledError:
                pass
            self._system_monitor_task = None
            logger.info("Stopped system monitoring")


# Global metrics instance
performance_metrics = PerformanceMetrics()


def track_performance(operation: str, module: str = "unknown"):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                performance_metrics.record_error(type(e).__name__, module)
                raise
            finally:
                duration = time.time() - start_time
                logger.debug(f"{module}.{operation} took {duration:.3f}s")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                performance_metrics.record_error(type(e).__name__, module)
                raise
            finally:
                duration = time.time() - start_time
                logger.debug(f"{module}.{operation} took {duration:.3f}s")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Convenience function to get metrics instance
def get_metrics() -> PerformanceMetrics:
    """Get the global performance metrics instance"""
    return performance_metrics