"""Metrics API routes."""

from fastapi import APIRouter
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus format for monitoring and alerting.
    """
    return generate_latest()


@router.get("/health")
async def metrics_health():
    """Metrics endpoint health check."""
    return {"status": "healthy", "endpoint": "metrics"}

