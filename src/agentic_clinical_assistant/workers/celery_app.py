"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from agentic_clinical_assistant.config import settings

# Create Celery app
celery_app = Celery(
    "agentic_clinical_assistant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "agentic_clinical_assistant.workers.tasks",
        "agentic_clinical_assistant.tools.workers",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Task routing
    task_routes={
        "agentic_clinical_assistant.workers.tasks.agent.*": {"queue": "agent"},
        "agentic_clinical_assistant.workers.tasks.ingestion.*": {"queue": "ingestion"},
        "agentic_clinical_assistant.workers.tasks.evaluation.*": {"queue": "evaluation"},
        "agentic_clinical_assistant.workers.tasks.benchmark.*": {"queue": "benchmark"},
    },
    # Priority queues
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "nightly-evaluation": {
            "task": "agentic_clinical_assistant.workers.tasks.evaluation.run_nightly_evaluation",
            "schedule": crontab(hour=2, minute=0),  # 2 AM daily
            "options": {"queue": "evaluation"},
        },
    },
)

