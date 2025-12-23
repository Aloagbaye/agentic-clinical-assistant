# Agent Memory System

The memory system provides session memory and policy memory for the agentic clinical assistant.

## Overview

The memory system consists of two main components:

1. **Session Memory**: User preferences and session context
2. **Policy Memory**: Frequently used documents and query patterns

**Important**: The memory system does NOT store any patient data (PHI/PII). Only document hashes, metadata, and query patterns are stored.

## Session Memory

Session memory stores user preferences and session context.

### Features

- **User Preferences**: Display format, jurisdiction, department, preferred backend
- **Session Expiration**: Automatic expiration after 30 days (configurable)
- **Context Storage**: General context (NO patient data)
- **Preference Application**: Preferences automatically applied to agent workflows

### Usage

```python
from agentic_clinical_assistant.memory.session import get_session_memory

session_memory = get_session_memory()

# Create session
session = await session_memory.create_session(
    user_id="user123",
    preferences={
        "display_format": "markdown",
        "department": "ER",
        "jurisdiction": "US",
        "preferred_backend": "faiss"
    }
)

# Get session
session = await session_memory.get_session(session_id)

# Update preferences
session = await session_memory.update_preferences(
    session_id,
    {"department": "ICU"}
)

# Get preferences
preferences = await session_memory.get_preferences(session_id)
```

### API Endpoints

- `POST /memory/sessions` - Create session
- `GET /memory/sessions/{session_id}` - Get session
- `PUT /memory/sessions/{session_id}/preferences` - Update preferences

## Policy Memory

Policy memory tracks document usage and query patterns.

### Features

- **Document Tracking**: Access counts, usage patterns
- **Query Patterns**: Common query types and templates
- **Policy Aliases**: Alternative names for policies
- **Success Tracking**: Success rates for queries

### Usage

```python
from agentic_clinical_assistant.memory.policy import get_policy_memory

policy_memory = get_policy_memory()

# Record document access
memory = await policy_memory.record_document_access(
    doc_hash="abc123...",
    document_id="doc_001",
    query_type="policy_lookup"
)

# Get frequently used documents
docs = await policy_memory.get_frequently_used_documents(limit=10)

# Add policy alias
memory = await policy_memory.add_policy_alias(
    doc_hash="abc123...",
    alias="sepsis_policy"
)

# Resolve alias
memory = await policy_memory.resolve_alias("sepsis_policy")
```

### API Endpoints

- `GET /memory/policy/frequently-used` - Get frequently used documents
- `POST /memory/policy/aliases` - Add policy alias
- `GET /memory/policy/aliases/{alias}` - Resolve alias

## Integration with Agents

### Intake Agent

The Intake Agent automatically loads user preferences from session memory:

```python
# Preferences are automatically loaded and applied
plan = await intake_agent.classify_request(
    request_text="...",
    user_id="user123",
    session_id=session_id
)
```

### Retrieval Agent

The Retrieval Agent uses preferred backend from session memory:

```python
# Preferred backend is automatically used
result = await retrieval_agent.retrieve_evidence(
    query="...",
    preferred_backend="faiss"  # From session preferences
)
```

## Database Schema

### SessionMemory

- `session_id`: Primary key
- `user_id`: User identifier
- `display_format`: Preferred output format
- `jurisdiction`: User's jurisdiction
- `department`: User's department
- `preferred_backend`: Preferred vector backend
- `preferences`: Additional preferences (JSON)
- `expires_at`: Session expiration
- `context`: General context (NO patient data)

### PolicyMemory

- `memory_id`: Primary key
- `doc_hash`: Document hash (NOT content)
- `document_id`: Document identifier
- `access_count`: Number of accesses
- `query_patterns`: Query type usage (JSON)
- `aliases`: Policy aliases
- `metadata`: Document metadata (NO patient data)

### QueryPattern

- `pattern_id`: Primary key
- `query_type`: Type of query
- `query_template`: Template pattern (NO patient data)
- `usage_count`: Usage statistics
- `success_rate`: Success rate
- `common_backends`: Most used backends
- `common_filters`: Common filters

## Security & Privacy

**Critical**: The memory system is designed to NEVER store patient data:

- ✅ Document hashes (not content)
- ✅ Query templates (not actual queries with PHI)
- ✅ Metadata (document metadata only)
- ✅ Usage statistics
- ❌ Patient names, SSNs, or any PHI
- ❌ Actual query text with patient data
- ❌ Document content

## Cleanup

Expired sessions are automatically cleaned up:

```python
# Clean up expired sessions
count = await session_memory.cleanup_expired_sessions()
print(f"Cleaned up {count} expired sessions")
```

## Testing

Run memory tests:

```bash
pytest tests/test_memory.py -v
```

## Next Steps

- Add memory learning algorithms
- Implement query pattern matching
- Add memory-based backend selection
- Implement preference inheritance

