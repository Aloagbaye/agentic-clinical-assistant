# Script to run Celery worker (PowerShell)

$queues = "default,agent,ingestion,evaluation,benchmark"

Write-Host "Starting Celery worker..." -ForegroundColor Cyan
Write-Host "Queues: $queues" -ForegroundColor Yellow

celery -A agentic_clinical_assistant.workers.celery_app worker `
    --loglevel=info `
    --concurrency=4 `
    --queues=$queues

