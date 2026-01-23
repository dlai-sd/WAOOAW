"""
Prometheus metrics setup for monitoring API performance
"""

from prometheus_client import Counter, Histogram, start_http_server
from core.config import settings

# Metrics
REQUEST_COUNT = Counter('request_count', 'Total number of requests')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds')
ERROR_COUNT = Counter('error_count', 'Total number of errors')

def start_metrics_server():
    """Start the Prometheus metrics server."""
    if settings.PROMETHEUS_METRICS_ENABLED:
        start_http_server(settings.PROMETHEUS_METRICS_PORT)

def record_request(latency: float, success: bool):
    """Record a request with its latency and success status."""
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(latency)
    if not success:
        ERROR_COUNT.inc()
