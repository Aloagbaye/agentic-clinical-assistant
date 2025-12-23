# Database Module

This module contains the database schema, models, and audit logging utilities for the agentic clinical assistant.

## Structure

```
database/
├── __init__.py           # Module exports
├── base.py               # Base configuration and session management
├── session.py            # Session exports
├── audit.py              # Audit logging service
├── models/               # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── agent_run.py      # Agent run logs
│   ├── tool_call.py      # Tool call records
│   ├── evidence_retrieval.py  # Evidence retrieval logs
│   ├── prompt_version.py # Prompt version tracking
│   ├── citation.py       # Citation mappings
│   ├── grounding_verification.py  # Grounding verification results
│   └── evaluation.py     # Evaluation outcomes
└── README.md             # This file
```

## Database Schema

### Tables

1. **agent_runs** - Tracks agent execution runs
   - `run_id` (UUID, PK)
   - `status` (enum: pending, running, completed, failed, abstained)
   - `user_id` (string, optional)
   - `request_text` (text)
   - `request_type` (string, optional)
   - `risk_label` (string, optional)
   - `final_answer` (text, optional)
   - `abstention_reason` (text, optional)
   - Timestamps: `created_at`, `started_at`, `completed_at`

2. **tool_calls** - Records all tool invocations
   - `tool_call_id` (UUID, PK)
   - `run_id` (UUID, FK → agent_runs)
   - `tool_name` (string)
   - `backend` (string, optional)
   - `inputs` (JSON)
   - `outputs` (JSON, optional)
   - `duration_ms` (float)
   - `success` (string: "true"/"false")
   - `error_message` (text, optional)

3. **evidence_retrievals** - Logs evidence retrieval operations
   - `retrieval_id` (UUID, PK)
   - `run_id` (UUID, FK → agent_runs)
   - `tool_call_id` (UUID, FK → tool_calls, optional)
   - `query` (text)
   - `backend` (string: faiss/pinecone/weaviate)
   - `retrieval_mode` (string: vector/hybrid/keyword)
   - `top_k` (integer)
   - `filters` (JSON, optional)
   - `scores` (JSON, optional)
   - `doc_hashes` (JSON) - List of document hashes

4. **prompt_versions** - Tracks prompt template versions
   - `version_id` (UUID, PK)
   - `prompt_name` (string)
   - `version` (string)
   - `template` (text)
   - `model` (string)
   - `parameters` (JSON, optional)
   - `is_active` (string: "true"/"false")

5. **citations** - Maps claims to sources
   - `citation_id` (UUID, PK)
   - `run_id` (UUID, FK → agent_runs)
   - `retrieval_id` (UUID, FK → evidence_retrievals, optional)
   - `claim_text` (text)
   - `claim_position` (integer, optional)
   - `doc_hash` (string) - SHA-256 hash
   - `doc_title` (string, optional)
   - `doc_section` (string, optional)
   - `relevance_score` (string, optional)

6. **grounding_verifications** - Stores verification results
   - `verification_id` (UUID, PK)
   - `run_id` (UUID, FK → agent_runs)
   - `status` (string: pass/fail/partial)
   - `passed` (string: "true"/"false")
   - `total_claims` (string)
   - `grounded_claims` (string)
   - `ungrounded_claims` (JSON, optional)
   - `issues` (JSON, optional)
   - `phi_redaction_count` (string)
   - `prompt_injection_detected` (string: "true"/"false")

7. **evaluations** - Stores evaluation/benchmark results
   - `evaluation_id` (UUID, PK)
   - `benchmark_id` (string)
   - `eval_set_id` (string, optional)
   - `backend` (string)
   - `mrr` (float) - Mean Reciprocal Rank
   - `ndcg` (float) - Normalized Discounted Cumulative Gain
   - `recall_at_k` (float)
   - `precision_at_k` (float)
   - `avg_latency_ms` (float)

## Usage

### Database Connection

```python
from agentic_clinical_assistant.database import get_async_session

async with get_async_session() as session:
    # Use session for database operations
    pass
```

### Audit Logging

```python
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database import get_async_session

async with get_async_session() as session:
    audit = AuditLogger(session)
    
    # Log agent run
    run_id = await audit.log_agent_run(
        request_text="What is the policy for X?",
        user_id="user123"
    )
    
    # Log tool call
    tool_call_id = await audit.log_tool_call(
        run_id=run_id,
        tool_name="retrieve_evidence",
        inputs={"query": "policy X", "backend": "faiss"},
        backend="faiss"
    )
    
    # Log evidence retrieval
    retrieval_id = await audit.log_evidence_retrieval(
        run_id=run_id,
        query="policy X",
        backend="faiss",
        doc_hashes=["hash1", "hash2"],
        top_k=10
    )
    
    # Log citation
    await audit.log_citation(
        run_id=run_id,
        claim_text="Policy X states...",
        doc_hash="hash1",
        doc_title="Policy Document X"
    )
    
    # Log grounding verification
    await audit.log_grounding_verification(
        run_id=run_id,
        status="pass",
        passed=True,
        total_claims=5,
        grounded_claims=5
    )
    
    await session.commit()
```

## Migrations

### Create Migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1
```

## Design Decisions

1. **UUIDs for Primary Keys**: All tables use UUIDs for primary keys to support distributed systems and avoid ID enumeration attacks.

2. **String Booleans**: Some fields use "true"/"false" strings instead of booleans for compatibility with JSON serialization and flexibility.

3. **JSON Fields**: Flexible JSON fields (`metadata`, `inputs`, `outputs`) allow for schema evolution without migrations.

4. **Audit Trail**: Every operation is logged with timestamps and relationships, enabling full traceability.

5. **Document Hashes**: Documents are referenced by SHA-256 hashes rather than storing content, ensuring data integrity and avoiding PHI storage.

6. **Async/Await**: All database operations use async/await for better performance with I/O-bound operations.

