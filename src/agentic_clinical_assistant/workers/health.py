"""Worker health check utilities."""

from typing import Any, Dict

from agentic_clinical_assistant.workers.celery_app import celery_app


def get_worker_stats() -> Dict[str, Any]:
    """
    Get Celery worker statistics.

    Returns:
        Dictionary with worker stats
    """
    inspect = celery_app.control.inspect()

    # Get active workers
    active_workers = inspect.active()
    registered_tasks = inspect.registered()
    stats = inspect.stats()

    return {
        "active_workers": active_workers or {},
        "registered_tasks": registered_tasks or {},
        "stats": stats or {},
    }


def check_worker_health() -> Dict[str, Any]:
    """
    Check worker health.

    Returns:
        Health status
    """
    inspect = celery_app.control.inspect()
    ping_result = inspect.ping()

    if ping_result:
        return {
            "status": "healthy",
            "workers_online": len(ping_result),
            "workers": list(ping_result.keys()),
        }
    else:
        return {
            "status": "unhealthy",
            "workers_online": 0,
            "workers": [],
        }

