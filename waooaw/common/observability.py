"""
Observability Module

Provides tracing, metrics, and logging integration for WAOOAW platform.
"""
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time
import logging
from contextlib import contextmanager

from waooaw.common.metrics import MetricsCollector


logger = logging.getLogger(__name__)


class Tracer:
    """Distributed tracing for request tracking."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.current_span: Optional[str] = None
    
    @contextmanager
    def span(self, name: str, tags: Optional[Dict[str, Any]] = None):
        """Create a tracing span.
        
        Args:
            name: Span name
            tags: Additional span tags
        """
        span_id = f"{name}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Store previous span
        previous_span = self.current_span
        self.current_span = span_id
        
        try:
            logger.debug(f"Starting span: {name}", extra={
                "span_id": span_id,
                "tags": tags or {}
            })
            yield span_id
        except Exception as e:
            logger.error(f"Span error: {name}", extra={
                "span_id": span_id,
                "error": str(e)
            })
            raise
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            histogram = self.metrics.histogram(
                f"span_duration_seconds_{name}",
                f"Duration of {name} span"
            )
            histogram.observe(duration)
            
            logger.debug(f"Completed span: {name}", extra={
                "span_id": span_id,
                "duration_ms": duration * 1000
            })
            
            # Restore previous span
            self.current_span = previous_span


def traced(span_name: Optional[str] = None):
    """Decorator to trace function execution.
    
    Args:
        span_name: Custom span name (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        name = span_name or func.__name__
        tracer = Tracer()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.span(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class StructuredLogger:
    """Structured logging with context."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set logging context."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context."""
        self.context.clear()
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method."""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)


class PerformanceMonitor:
    """Monitor application performance."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
    
    @contextmanager
    def measure(self, operation: str):
        """Measure operation duration.
        
        Args:
            operation: Operation name
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # Record to histogram
            histogram = self.metrics.histogram(
                f"operation_duration_seconds",
                "Operation duration in seconds",
                labelnames=["operation"]
            )
            histogram.labels(operation=operation).observe(duration)
            
            # Log slow operations
            if duration > 1.0:  # 1 second threshold
                logger.warning(f"Slow operation: {operation}", extra={
                    "operation": operation,
                    "duration_ms": duration * 1000
                })


class HealthReporter:
    """Report application health status."""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.metrics = MetricsCollector()
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check.
        
        Args:
            name: Check name
            check_func: Function that returns True if healthy
        """
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, bool]:
        """Run all health checks.
        
        Returns:
            Dictionary of check results
        """
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
                
                # Record metric
                gauge = self.metrics.gauge(
                    f"health_check",
                    "Health check status",
                    labelnames=["check"]
                )
                gauge.labels(check=name).set(1 if result else 0)
                
            except Exception as e:
                logger.error(f"Health check failed: {name}", extra={
                    "check": name,
                    "error": str(e)
                })
                results[name] = False
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if all health checks pass.
        
        Returns:
            True if all checks pass
        """
        results = self.run_checks()
        return all(results.values())


# Global instances
tracer = Tracer()
performance_monitor = PerformanceMonitor()
health_reporter = HealthReporter()


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
