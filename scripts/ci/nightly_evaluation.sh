#!/bin/bash
# Nightly evaluation job script

set -e

echo "Starting nightly evaluation job..."

# Set environment
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://user:pass@localhost:5432/db}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"

# Run evaluation
python -m agentic_clinical_assistant.workers.tasks.evaluation run_nightly_evaluation

# Publish results to Prometheus (if using push gateway)
if [ -n "$PROMETHEUS_PUSHGATEWAY" ]; then
    echo "Publishing results to Prometheus..."
    # Add push gateway logic here
fi

echo "Nightly evaluation completed"

