#!/bin/bash
# Script to run Celery worker

celery -A agentic_clinical_assistant.workers.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=default,agent,ingestion,evaluation,benchmark

