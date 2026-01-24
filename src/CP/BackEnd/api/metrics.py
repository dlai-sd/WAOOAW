"""
Prometheus Metrics Endpoint
Exposes application metrics for Prometheus scraping.
"""

from fastapi import APIRouter
from prometheus_client import generate_latest, CollectorRegistry

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Expose metrics for Prometheus."""
    registry = CollectorRegistry()
    return generate_latest(registry)
