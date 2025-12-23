"""Worker package for agentic-clinical-assistant."""

from agentic_clinical_assistant.workers.celery_app import celery_app

__all__ = ["celery_app"]

