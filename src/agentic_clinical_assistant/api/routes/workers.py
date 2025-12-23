"""Worker health and monitoring routes."""

from typing import Dict

from fastapi import APIRouter

from agentic_clinical_assistant.workers.health import check_worker_health, get_worker_stats

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/health")
async def worker_health() -> Dict[str, Any]:
    """
    Worker health check endpoint.

    Returns the health status of Celery workers.
    """
    return check_worker_health()


@router.get("/stats")
async def worker_stats() -> Dict[str, Any]:
    """
    Worker statistics endpoint.

    Returns statistics about active workers and registered tasks.
    """
    return get_worker_stats()

