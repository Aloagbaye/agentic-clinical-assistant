# Phase 2 Tutorial: Agent Orchestrator API & Worker Infrastructure

This tutorial covers Phase 2 of the PHI-Safe Clinical Ops Copilot project, which includes the Agent Orchestrator API (FastAPI) and Tool Worker Infrastructure (Celery).

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 2.1: Agent Orchestrator API](#phase-21-agent-orchestrator-api)
4. [Phase 2.2: Tool Worker Infrastructure](#phase-22-tool-worker-infrastructure)
5. [Running the Complete System](#running-the-complete-system)
6. [API Usage Examples](#api-usage-examples)
7. [Worker Task Examples](#worker-task-examples)
8. [Troubleshooting](#troubleshooting)

## Overview

Phase 2 implements the core infrastructure for the agentic clinical assistant:

- **Agent Orchestrator API**: FastAPI-based REST API for initiating and monitoring agent runs
- **Tool Worker Infrastructure**: Celery-based asynchronous task processing for agent workflows

### Architecture

```
┌─────────────────┐
│   FastAPI API   │  ← Phase 2.1: REST endpoints
└────────┬────────┘
         │
         │ Dispatches tasks
         ▼
┌─────────────────┐
│  Celery Worker  │  ← Phase 2.2: Async task processing
└────────┬────────┘
         │
         │ Executes workflows
         ▼
┌─────────────────┐
│  Agent Workflow │  ← Phase 2.3 (Future)
└─────────────────┘
```

## Prerequisites

Before starting, ensure you have:

1. **Python 3.10+** installed
2. **PostgreSQL** running (via Docker Compose)
3. **Redis** running (via Docker Compose)
4. **Environment variables** configured (`.env` file)

### Setup Steps

1. **Start required services:**
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Initialize database:**
   ```bash
   python scripts/init_db.py
   alembic upgrade head
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Phase 2.1: Agent Orchestrator API

The Agent Orchestrator API provides REST endpoints for managing agent runs.

### Starting the API Server

**Option 1: Using the script**
```bash
python scripts/run_api.py
```

**Option 2: Using Makefile**
```bash
make run-api
```

**Option 3: Direct uvicorn**
```bash
uvicorn agentic_clinical_assistant.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Root Endpoint

```bash
GET /
```

**Response:**
```json
{
  "service": "PHI-Safe Clinical Ops Copilot",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs"
}
```

#### 2. Start Agent Run

```bash
POST /agent/run
Content-Type: application/json

{
  "request_text": "What is the policy for sepsis treatment?",
  "user_id": "user123",
  "metadata": {
    "department": "ER",
    "priority": "high"
  }
}
```

**Response (202 Accepted):**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z",
  "message": "Agent run initiated successfully"
}
```

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/agent/run" \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "What is the policy for sepsis treatment?",
    "user_id": "user123"
  }'
```

#### 3. Check Agent Run Status

```bash
GET /agent/status/{run_id}
```

**Response:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "request_text": "What is the policy for sepsis treatment?",
  "request_type": "policy_lookup",
  "risk_label": "low",
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:01Z",
  "completed_at": null,
  "final_answer": null,
  "progress": {
    "current_step": "retrieval",
    "steps_completed": 2,
    "total_steps": 4
  }
}
```

**Example using curl:**
```bash
curl "http://localhost:8000/agent/status/550e8400-e29b-41d4-a716-446655440000"
```

#### 4. Worker Health Check

```bash
GET /workers/health
```

**Response:**
```json
{
  "status": "healthy",
  "workers_online": 2,
  "workers": ["worker1@hostname", "worker2@hostname"]
}
```

#### 5. Worker Statistics

```bash
GET /workers/stats
```

**Response:**
```json
{
  "active_workers": {
    "worker1@hostname": {
      "active": []
    }
  },
  "registered_tasks": {
    "worker1@hostname": [
      "agentic_clinical_assistant.workers.tasks.agent.run_agent_workflow",
      "agentic_clinical_assistant.workers.tasks.agent.run_intake_agent",
      ...
    ]
  }
}
```

#### 6. Prometheus Metrics

```bash
GET /metrics
```

Returns metrics in Prometheus format for monitoring.

### API Documentation

Once the API is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Phase 2.2: Tool Worker Infrastructure

The Tool Worker Infrastructure uses Celery for asynchronous task processing.

### Starting Celery Workers

**Option 1: Using the script**
```bash
python scripts/run_worker.py
```

**Option 2: Using Makefile**
```bash
make run-worker
```

**Option 3: Direct celery command**
```bash
celery -A agentic_clinical_assistant.workers.celery_app worker --loglevel=info
```

**With specific queues:**
```bash
celery -A agentic_clinical_assistant.workers.celery_app worker \
  --queues=agent,ingestion \
  --concurrency=4
```

### Task Queues

Tasks are automatically routed to different queues:

- **`default`**: General tasks
- **`agent`**: Agent workflow tasks
- **`ingestion`**: Document ingestion tasks
- **`evaluation`**: Evaluation/benchmarking tasks
- **`benchmark`**: Performance benchmarking

### Starting Celery Beat (Scheduler)

For scheduled tasks (e.g., nightly evaluation):

```bash
python scripts/run_beat.py
```

Or:
```bash
celery -A agentic_clinical_assistant.workers.celery_app beat --loglevel=info
```

### Available Tasks

#### Agent Tasks

1. **`run_agent_workflow`**: Main workflow orchestrator
   - Orchestrates the full agent workflow
   - Coordinates Intake → Retrieval → Synthesis → Verifier

2. **`run_intake_agent`**: Request classification
   - Classifies the request type
   - Assesses risk level
   - Determines required tools

3. **`run_retrieval_agent`**: Evidence retrieval
   - Searches vector databases
   - Retrieves relevant evidence
   - Filters by metadata

4. **`run_synthesis_agent`**: Answer generation
   - Generates draft answer
   - Includes citations
   - Formats response

5. **`run_verifier_agent`**: Safety verification
   - Verifies safety and grounding
   - Checks for PHI leakage
   - Validates citations

#### Ingestion Tasks

1. **`ingest_documents`**: Batch document ingestion
   - Processes documents in batches
   - Generates embeddings
   - Adds to vector database

2. **`reindex_documents`**: Vector DB reindexing
   - Reindexes all documents
   - Updates embeddings

#### Evaluation Tasks

1. **`run_evaluation`**: Backend benchmarking
   - Runs evaluation on vector backends
   - Computes metrics (MRR, nDCG, Recall@k)

2. **`run_nightly_evaluation`**: Scheduled evaluation
   - Runs automatically at 2 AM daily
   - Publishes results

## Running the Complete System

### Step-by-Step Setup

1. **Start infrastructure services:**
   ```bash
   docker-compose up -d
   ```

2. **Start the API server (Terminal 1):**
   ```bash
   python scripts/run_api.py
   ```

3. **Start Celery worker (Terminal 2):**
   ```bash
   python scripts/run_worker.py
   ```

4. **Start Celery Beat (Terminal 3, optional):**
   ```bash
   python scripts/run_beat.py
   ```

### Verification

1. **Check API health:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Check worker health:**
   ```bash
   curl http://localhost:8000/workers/health
   ```

3. **View API documentation:**
   - Open `http://localhost:8000/docs` in your browser

## API Usage Examples

### Example 1: Start an Agent Run

```python
import requests

# Start an agent run
response = requests.post(
    "http://localhost:8000/agent/run",
    json={
        "request_text": "What is the policy for sepsis treatment?",
        "user_id": "doctor123",
        "metadata": {
            "department": "ER",
            "priority": "high"
        }
    }
)

run_data = response.json()
run_id = run_data["run_id"]
print(f"Agent run started: {run_id}")
```

### Example 2: Poll for Status

```python
import requests
import time

run_id = "550e8400-e29b-41d4-a716-446655440000"

while True:
    response = requests.get(f"http://localhost:8000/agent/status/{run_id}")
    status_data = response.json()
    
    print(f"Status: {status_data['status']}")
    
    if status_data["status"] in ["completed", "failed", "abstained"]:
        if status_data.get("final_answer"):
            print(f"Answer: {status_data['final_answer']}")
        break
    
    time.sleep(2)  # Poll every 2 seconds
```

### Example 3: Using Python Client

```python
from agentic_clinical_assistant.api.models.agent import AgentRunRequest
from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger

async def start_agent_run(request_text: str, user_id: str = None):
    async for session in get_async_session():
        audit = AuditLogger(session)
        
        # Log agent run
        run_id = await audit.log_agent_run(
            request_text=request_text,
            user_id=user_id,
        )
        
        await session.commit()
        return run_id
```

## Worker Task Examples

### Example 1: Dispatch Agent Workflow Task

```python
from agentic_clinical_assistant.workers.tasks.agent import run_agent_workflow
import uuid

# Dispatch task
run_id = uuid.uuid4()
task = run_agent_workflow.delay(
    run_id=run_id,
    request_text="What is the policy for sepsis treatment?",
    user_id="doctor123"
)

# Get result (blocking)
result = task.get(timeout=300)  # 5 minute timeout
print(f"Workflow completed: {result}")
```

### Example 2: Dispatch Ingestion Task

```python
from agentic_clinical_assistant.workers.tasks.ingestion import ingest_documents

documents = [
    {
        "text": "Sepsis treatment protocol...",
        "metadata": {
            "source": "policy_doc_001",
            "department": "ER"
        }
    },
    {
        "text": "Emergency response guidelines...",
        "metadata": {
            "source": "policy_doc_002",
            "department": "ER"
        }
    }
]

# Dispatch ingestion task
task = ingest_documents.delay(
    documents=documents,
    backend="faiss",
    batch_size=100
)

# Get result
result = task.get()
print(f"Ingested {result['ingested_count']} documents")
```

### Example 3: Chain Tasks

```python
from agentic_clinical_assistant.workers.tasks.agent import (
    run_intake_agent,
    run_retrieval_agent,
    run_synthesis_agent,
    run_verifier_agent
)
from celery import chain
import uuid

run_id = uuid.uuid4()
request_text = "What is the policy for sepsis treatment?"

# Chain tasks
workflow = chain(
    run_intake_agent.s(run_id, request_text),
    run_retrieval_agent.s(),
    run_synthesis_agent.s(),
    run_verifier_agent.s()
)

# Execute chain
result = workflow.apply_async()
final_result = result.get()
```

## Monitoring

### Worker Monitoring with Flower

Install Flower:
```bash
pip install flower
```

Start Flower:
```bash
celery -A agentic_clinical_assistant.workers.celery_app flower
```

Access Flower UI at `http://localhost:5555`

### Prometheus Metrics

The API exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Database Monitoring

Check agent runs in the database:

```python
from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.models.agent_run import AgentRun

async def get_recent_runs():
    async for session in get_async_session():
        runs = await session.query(AgentRun).order_by(
            AgentRun.created_at.desc()
        ).limit(10).all()
        
        for run in runs:
            print(f"{run.run_id}: {run.status} - {run.request_text[:50]}")
```

## Troubleshooting

### Issue: Worker won't start

**Symptoms:**
- `ModuleNotFoundError` when starting worker
- Import errors

**Solutions:**
1. Ensure package is installed: `pip install -e .`
2. Check Python version: `python --version` (should be 3.10+)
3. Verify dependencies: `pip list | grep celery`

### Issue: Redis connection error

**Symptoms:**
- `ConnectionRefusedError` when starting worker
- Worker can't connect to broker

**Solutions:**
1. Check Redis is running: `docker-compose ps`
2. Verify Redis URL in `.env`: `CELERY_BROKER_URL=redis://localhost:6379/0`
3. Test connection: `redis-cli ping`

### Issue: Database connection error

**Symptoms:**
- `ConnectionRefusedError` when calling API
- Database errors in logs

**Solutions:**
1. Check PostgreSQL is running: `docker-compose ps`
2. Verify database URL in `.env`
3. Test connection: `python scripts/init_db.py`

### Issue: Tasks not executing

**Symptoms:**
- Tasks queued but not processed
- Worker shows no activity

**Solutions:**
1. Check worker is consuming correct queue: `--queues=agent`
2. Verify task routing in `celery_app.py`
3. Check worker logs for errors

### Issue: Import errors with sentence-transformers

**Symptoms:**
- `ModuleNotFoundError: No module named 'h5py'`
- `ModuleNotFoundError: No module named 'tf_keras'`

**Solutions:**
1. Install missing dependencies:
   ```bash
   pip install h5py tf-keras
   ```
2. Reinstall package: `pip install -e .`

## Next Steps

After completing Phase 2, you can:

1. **Phase 2.3**: Implement the workflow engine to connect API and workers
2. **Phase 3**: Build the agent implementations (Intake, Retrieval, Synthesis, Verifier)
3. **Phase 4**: Implement tools and tool workers

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Project README](../README.md)
- [Database Setup Guide](database-setup.md)
- [Vector Database Guide](phase-1.3-vector-databases.md)

## Summary

Phase 2 provides:

✅ REST API for agent orchestration  
✅ Asynchronous task processing with Celery  
✅ Worker health monitoring  
✅ Task routing and priority queues  
✅ Prometheus metrics integration  
✅ Database audit logging  

The system is now ready for Phase 2.3 (Workflow Engine) to connect the API and workers into a complete agent workflow system.

