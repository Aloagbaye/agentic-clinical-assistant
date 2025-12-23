# Phase 1.2: Database Schema & Audit Layer

This document explains the database schema and audit layer implementation completed in Phase 1.2.

## Overview

Phase 1.2 establishes the PostgreSQL database schema, SQLAlchemy ORM models, Alembic migrations, and comprehensive audit logging system for tracking all agent operations.

## Database Architecture

### Schema Design Principles

1. **Full Auditability**: Every operation is logged with timestamps and relationships
2. **UUID Primary Keys**: All tables use UUIDs for distributed system compatibility
3. **Flexible Metadata**: JSON fields allow schema evolution without migrations
4. **Document Integrity**: Documents referenced by SHA-256 hashes (no PHI storage)
5. **Async Operations**: All database operations use async/await for performance

## Database Tables

### 1. agent_runs

Tracks agent execution runs from start to completion.

**Key Fields:**
- `run_id` (UUID): Unique identifier for the run
- `status` (enum): pending, running, completed, failed, abstained
- `request_text` (text): User's original request
- `request_type` (string): Classification (e.g., "policy_lookup", "summarize")
- `risk_label` (string): Risk classification (low/medium/high)
- `final_answer` (text): Generated answer (if completed)
- `abstention_reason` (text): Reason for abstention (if applicable)

**Use Cases:**
- Track agent execution lifecycle
- Monitor success/failure rates
- Audit user requests
- Analyze request types and risk levels

### 2. tool_calls

Records all tool invocations during agent runs.

**Key Fields:**
- `tool_call_id` (UUID): Unique identifier
- `run_id` (UUID): Foreign key to agent_runs
- `tool_name` (string): Name of tool (e.g., "retrieve_evidence", "redact_phi")
- `backend` (string): Vector backend used (if applicable)
- `inputs` (JSON): Tool input parameters
- `outputs` (JSON): Tool output results
- `duration_ms` (float): Execution time
- `success` (string): "true" or "false"
- `error_message` (text): Error details if failed

**Use Cases:**
- Performance monitoring
- Debugging tool failures
- Analyzing tool usage patterns
- Backend comparison

### 3. evidence_retrievals

Logs evidence retrieval operations from vector databases.

**Key Fields:**
- `retrieval_id` (UUID): Unique identifier
- `run_id` (UUID): Foreign key to agent_runs
- `query` (text): Search query
- `backend` (string): Vector backend (faiss/pinecone/weaviate)
- `retrieval_mode` (string): vector/hybrid/keyword
- `top_k` (integer): Number of results requested
- `filters` (JSON): Metadata filters applied
- `scores` (JSON): Similarity scores
- `doc_hashes` (JSON): List of document hashes retrieved

**Use Cases:**
- Compare backend performance
- Analyze retrieval quality
- Track query patterns
- Debug retrieval issues

### 4. prompt_versions

Tracks prompt template versions for reproducibility.

**Key Fields:**
- `version_id` (UUID): Unique identifier
- `prompt_name` (string): Name of prompt (e.g., "synthesis_v1")
- `version` (string): Version number (e.g., "1.0", "2.1")
- `template` (text): Prompt template
- `model` (string): LLM model used
- `parameters` (JSON): Model parameters (temperature, max_tokens, etc.)
- `is_active` (string): "true" or "false"

**Use Cases:**
- Version control for prompts
- A/B testing different prompts
- Reproducibility
- Prompt optimization

### 5. citations

Maps claims in answers to their source documents.

**Key Fields:**
- `citation_id` (UUID): Unique identifier
- `run_id` (UUID): Foreign key to agent_runs
- `claim_text` (text): The claim being cited
- `claim_position` (integer): Position in answer
- `doc_hash` (string): SHA-256 hash of source document
- `doc_title` (string): Document title
- `doc_section` (string): Section reference
- `relevance_score` (string): Similarity score

**Use Cases:**
- Verify answer grounding
- Track source usage
- Generate citation lists
- Quality assurance

### 6. grounding_verifications

Stores verification results from the Verifier Agent.

**Key Fields:**
- `verification_id` (UUID): Unique identifier
- `run_id` (UUID): Foreign key to agent_runs
- `status` (string): pass/fail/partial
- `passed` (string): "true" or "false"
- `total_claims` (string): Number of claims checked
- `grounded_claims` (string): Number with citations
- `ungrounded_claims` (JSON): List of ungrounded claims
- `phi_redaction_count` (string): Number of PHI redactions
- `prompt_injection_detected` (string): "true" or "false"

**Use Cases:**
- Safety monitoring
- Quality metrics
- Compliance reporting
- Identifying hallucination patterns

### 7. evaluations

Stores evaluation/benchmark results for vector backends.

**Key Fields:**
- `evaluation_id` (UUID): Unique identifier
- `benchmark_id` (string): Evaluation run identifier
- `backend` (string): Backend evaluated
- `mrr` (float): Mean Reciprocal Rank
- `ndcg` (float): Normalized Discounted Cumulative Gain
- `recall_at_k` (float): Recall@k metric
- `precision_at_k` (float): Precision@k metric
- `avg_latency_ms` (float): Average retrieval latency

**Use Cases:**
- Backend comparison
- Performance tracking
- Quality metrics
- A/B testing results

## Audit Logging Service

The `AuditLogger` class provides a high-level interface for logging all operations.

### Usage Example

```python
from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database.models.agent_run import RunStatus

async with get_async_session() as session:
    audit = AuditLogger(session)
    
    # 1. Log agent run start
    run_id = await audit.log_agent_run(
        request_text="What is the policy for sepsis treatment?",
        user_id="user123",
        request_type="policy_lookup",
        risk_label="low"
    )
    
    # 2. Update status to running
    await audit.update_agent_run_status(run_id, RunStatus.RUNNING)
    
    # 3. Log tool call
    tool_call_id = await audit.log_tool_call(
        run_id=run_id,
        tool_name="retrieve_evidence",
        inputs={"query": "sepsis treatment", "backend": "faiss", "top_k": 10},
        backend="faiss",
        duration_ms=45.2
    )
    
    # 4. Log evidence retrieval
    retrieval_id = await audit.log_evidence_retrieval(
        run_id=run_id,
        query="sepsis treatment",
        backend="faiss",
        doc_hashes=["hash1", "hash2", "hash3"],
        top_k=10,
        scores=[0.95, 0.87, 0.82],
        tool_call_id=tool_call_id
    )
    
    # 5. Log citations
    await audit.log_citation(
        run_id=run_id,
        claim_text="Sepsis treatment requires immediate antibiotics",
        doc_hash="hash1",
        doc_title="Sepsis Treatment Protocol",
        retrieval_id=retrieval_id
    )
    
    # 6. Log grounding verification
    await audit.log_grounding_verification(
        run_id=run_id,
        status="pass",
        passed=True,
        total_claims=5,
        grounded_claims=5,
        phi_redaction_count=0
    )
    
    # 7. Update status to completed
    await audit.update_agent_run_status(
        run_id,
        RunStatus.COMPLETED,
        final_answer="Based on the protocol..."
    )
    
    await session.commit()
```

## Database Migrations

### Alembic Configuration

The project uses Alembic for database migrations. Configuration files:

- `alembic.ini`: Alembic configuration
- `alembic/env.py`: Migration environment setup
- `alembic/script.py.mako`: Migration template

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>
```

### Initial Migration

To create the initial migration:

```bash
# Windows
.\scripts\create_initial_migration.ps1

# Unix/Mac
bash scripts/create_initial_migration.sh

# Or manually
alembic revision --autogenerate -m "Initial schema"
```

## Database Initialization

### Initialize Database

```bash
# Create database if it doesn't exist
python scripts/init_db.py

# Or using Makefile
make init-db
```

### Setup Steps

1. **Create Database** (if needed):
   ```bash
   python scripts/init_db.py
   ```

2. **Create Initial Migration**:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

3. **Apply Migrations**:
   ```bash
   alembic upgrade head
   ```

## Connection Pooling

The database uses SQLAlchemy connection pooling:

- **Pool Size**: Configurable via `DATABASE_POOL_SIZE` (default: 10)
- **Max Overflow**: Configurable via `DATABASE_MAX_OVERFLOW` (default: 20)
- **Pre-ping**: Enabled to verify connections before use
- **Async Engine**: Uses `asyncpg` for async PostgreSQL operations

## Testing

Database tests use in-memory SQLite for speed:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from agentic_clinical_assistant.database.base import Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # ... test code
```

Run tests:

```bash
pytest tests/test_database.py
```

## Design Decisions

### Why UUIDs?

- **Distributed Systems**: UUIDs work across multiple database instances
- **Security**: Avoids ID enumeration attacks
- **Uniqueness**: Guaranteed uniqueness without coordination

### Why String Booleans?

Some fields use "true"/"false" strings instead of booleans:
- **JSON Compatibility**: Easier serialization/deserialization
- **Flexibility**: Can add "unknown" or other states later
- **Database Portability**: Works consistently across databases

### Why JSON Fields?

Flexible JSON fields (`metadata`, `inputs`, `outputs`):
- **Schema Evolution**: Add fields without migrations
- **Flexibility**: Store varying structures
- **Performance**: PostgreSQL has excellent JSON support

### Why Document Hashes?

Documents referenced by SHA-256 hashes:
- **PHI Safety**: No patient data stored in database
- **Integrity**: Verify document authenticity
- **Deduplication**: Identify duplicate documents
- **Compliance**: Meets regulatory requirements

## Next Steps

After completing Phase 1.2, proceed to:

- **Phase 1.3**: Vector Database Integration Layer
  - Implement FAISS adapter
  - Implement Pinecone adapter
  - Implement Weaviate adapter
  - Create unified interface

## Resources

- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL JSON Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)

