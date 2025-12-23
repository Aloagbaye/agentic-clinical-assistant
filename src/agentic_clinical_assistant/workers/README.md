# Worker Infrastructure

Celery-based worker infrastructure for asynchronous task processing.

## Overview

The worker infrastructure handles:
- Agent workflow execution
- Document ingestion
- Evaluation and benchmarking
- Long-running tasks

## Celery Configuration

### Queues

Tasks are routed to different queues based on type:

- **default**: General tasks
- **agent**: Agent workflow tasks
- **ingestion**: Document ingestion tasks
- **evaluation**: Evaluation/benchmarking tasks
- **benchmark**: Performance benchmarking

### Task Routing

Tasks are automatically routed based on their task name:

```python
task_routes = {
    "agentic_clinical_assistant.workers.tasks.agent.*": {"queue": "agent"},
    "agentic_clinical_assistant.workers.tasks.ingestion.*": {"queue": "ingestion"},
    "agentic_clinical_assistant.workers.tasks.evaluation.*": {"queue": "evaluation"},
}
```

## Running Workers

### Start Worker

```bash
# Using script
python scripts/run_worker.py

# Using Makefile
make run-worker

# Direct command
celery -A agentic_clinical_assistant.workers.celery_app worker --loglevel=info
```

### Start Worker with Specific Queues

```bash
celery -A agentic_clinical_assistant.workers.celery_app worker \
    --queues=agent,ingestion \
    --concurrency=4
```

### Start Celery Beat (Scheduler)

```bash
# For scheduled tasks (e.g., nightly evaluation)
python scripts/run_beat.py

# Or
celery -A agentic_clinical_assistant.workers.celery_app beat
```

## Task Definitions

### Agent Tasks

- `run_agent_workflow`: Main workflow orchestrator
- `run_intake_agent`: Request classification
- `run_retrieval_agent`: Evidence retrieval
- `run_synthesis_agent`: Answer generation
- `run_verifier_agent`: Safety verification

### Ingestion Tasks

- `ingest_documents`: Ingest documents into vector DB
- `reindex_documents`: Reindex vector database

### Evaluation Tasks

- `run_evaluation`: Run evaluation benchmark
- `run_nightly_evaluation`: Scheduled nightly evaluation

## Health Monitoring

### Worker Health Endpoint

```bash
GET /workers/health
```

Returns:
```json
{
  "status": "healthy",
  "workers_online": 2,
  "workers": ["worker1@hostname", "worker2@hostname"]
}
```

### Worker Stats Endpoint

```bash
GET /workers/stats
```

Returns detailed statistics about workers and tasks.

## Configuration

Set in `.env`:

```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Task Retry Logic

All tasks have automatic retry logic:

- **Max Retries**: 2-3 attempts
- **Retry Delay**: 60 seconds (exponential backoff)
- **Error Handling**: Tasks update run status on failure

## Production Deployment

For production:

1. **Multiple Workers**: Run workers on different machines
2. **Queue Separation**: Dedicated workers per queue type
3. **Monitoring**: Use Flower for Celery monitoring
4. **Scaling**: Scale workers based on queue depth

### Example Production Setup

```bash
# Agent worker (high priority)
celery -A agentic_clinical_assistant.workers.celery_app worker \
    --queues=agent \
    --concurrency=8 \
    --hostname=agent-worker@%h

# Ingestion worker
celery -A agentic_clinical_assistant.workers.celery_app worker \
    --queues=ingestion \
    --concurrency=4 \
    --hostname=ingestion-worker@%h

# Evaluation worker (low priority)
celery -A agentic_clinical_assistant.workers.celery_app worker \
    --queues=evaluation,benchmark \
    --concurrency=2 \
    --hostname=eval-worker@%h
```

## Monitoring with Flower

Install Flower for Celery monitoring:

```bash
pip install flower
```

Run Flower:

```bash
celery -A agentic_clinical_assistant.workers.celery_app flower
```

Access at: `http://localhost:5555`

## Next Steps

- Integrate with workflow engine (Phase 2.3)
- Add task result persistence
- Implement task prioritization
- Add task monitoring and alerting

