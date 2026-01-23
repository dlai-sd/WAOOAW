"""
Prometheus metrics endpoint for WAOOAW Customer Portal
"""

from fastapi import APIRouter
from prometheus_client import generate_latest, CollectorRegistry, Counter, Histogram

router = APIRouter()

# Create Prometheus metrics
registry = CollectorRegistry()
request_counter = Counter('request_count', 'Total request count', registry=registry)
latency_histogram = Histogram('request_latency_seconds', 'Request latency in seconds', registry=registry)
error_counter = Counter('error_count', 'Total error count', registry=registry)

@router.middleware("http")
async def add_metrics(request, call_next):
    """Middleware to track request metrics"""
    request_counter.inc()
    with latency_histogram.time():
        response = await call_next(request)
    if response.status_code >= 400:
        error_counter.inc()
    return response

@router.get("/metrics")
async def metrics():
    """Expose metrics for Prometheus"""
    return generate_latest(registry)
