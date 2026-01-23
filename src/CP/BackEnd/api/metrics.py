"""
Prometheus metrics endpoint for the API
"""

from fastapi import APIRouter
from prometheus_client import generate_latest, CollectorRegistry

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics"""
    registry = CollectorRegistry()
    return generate_latest(registry)
