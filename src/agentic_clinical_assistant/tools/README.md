# Tools

Core tools and workflow tools for the agentic clinical assistant system.

## Core Tools

### 1. retrieve_evidence

Retrieve evidence from vector databases.

**Parameters:**
- `query` (str): Search query
- `backend` (str, optional): Specific backend to use
- `filters` (dict, optional): Metadata filters
- `top_k` (int, default=10): Number of results

**Returns:**
- Evidence results with documents, scores, and metadata

**Example:**
```python
from agentic_clinical_assistant.tools.core import retrieve_evidence

result = await retrieve_evidence(
    query="sepsis treatment protocol",
    backend="faiss",
    filters={"department": "ER"},
    top_k=10
)
```

### 2. redact_phi

Redact PHI/PII from text.

**Parameters:**
- `text` (str): Text to redact
- `aggressive` (bool, default=False): Use aggressive redaction

**Returns:**
- Redacted text and redaction details

**Example:**
```python
from agentic_clinical_assistant.tools.core import redact_phi

result = await redact_phi(
    text="Patient SSN: 123-45-6789",
    aggressive=True
)
print(result["redacted_text"])  # "Patient SSN: [SSN]"
```

### 3. run_backend_benchmark

Run benchmark evaluation on vector backends.

**Parameters:**
- `eval_set_id` (str): Evaluation dataset ID
- `backends` (list, optional): Backends to evaluate
- `benchmark_id` (str, optional): Benchmark run ID

**Returns:**
- Benchmark results with metrics

**Example:**
```python
from agentic_clinical_assistant.tools.core import run_backend_benchmark

result = await run_backend_benchmark(
    eval_set_id="eval_001",
    backends=["faiss", "pinecone"]
)
```

### 4. generate_answer

Generate answer from evidence bundle.

**Parameters:**
- `evidence_bundle` (list): Evidence items
- `request_text` (str): User request
- `prompt_version` (str, optional): Prompt version
- `model` (str, optional): LLM model

**Returns:**
- Generated answer with citations

**Example:**
```python
from agentic_clinical_assistant.tools.core import generate_answer

result = await generate_answer(
    evidence_bundle=[...],
    request_text="What is the policy?",
    prompt_version="v1.0"
)
```

### 5. verify_grounding

Verify grounding of answer in evidence.

**Parameters:**
- `draft_answer` (str): Draft answer
- `evidence_bundle` (list): Evidence items

**Returns:**
- Verification result with pass/fail status

**Example:**
```python
from agentic_clinical_assistant.tools.core import verify_grounding

result = await verify_grounding(
    draft_answer="According to policy...",
    evidence_bundle=[...]
)
print(f"Passed: {result['passed']}")
```

## Workflow Tools

### 1. build_checklist

Build structured checklist from procedure answer.

**Parameters:**
- `answer_text` (str): Answer text
- `format` (str, default="json"): Output format (json/markdown/html)

**Returns:**
- Checklist in requested format

**Example:**
```python
from agentic_clinical_assistant.tools.workflow import build_checklist

result = await build_checklist(
    answer_text="Step 1: Administer antibiotics. Step 2: Monitor vitals.",
    format="json"
)
```

### 2. extract_workflow_actions

Extract workflow actions from answer.

**Parameters:**
- `answer_text` (str): Answer text
- `format` (str, default="json"): Output format

**Returns:**
- Workflow actions in requested format

## Tool Registry

The tool registry manages all available tools:

```python
from agentic_clinical_assistant.tools.registry import get_registry

registry = get_registry()

# List all tools
tools = registry.list_tools()

# Get specific tool
tool = registry.get_tool("retrieve_evidence")

# Execute tool
result = await registry.execute_tool("retrieve_evidence", query="test", top_k=5)
```

## Tool Workers

Tools can be executed as Celery tasks:

```python
from agentic_clinical_assistant.tools.workers.core import tool_retrieve_evidence

# Dispatch as Celery task
task = tool_retrieve_evidence.delay(
    query="sepsis treatment",
    top_k=10
)

# Get result
result = task.get()
```

## API Endpoints

### List Tools

```bash
GET /tools
```

### Get Tool Info

```bash
GET /tools/{tool_name}
```

### Execute Tool

```bash
POST /tools/{tool_name}/execute
Content-Type: application/json

{
  "query": "sepsis treatment",
  "top_k": 10
}
```

## Integration

Tools are integrated with:

- **Agents**: Tools are called by agents during workflow execution
- **Workflow Engine**: Tools are invoked as part of agent steps
- **Database**: All tool calls are logged to audit tables
- **Celery**: Tools can run as async tasks

## Testing

Run tool tests:

```bash
pytest tests/test_tools.py -v
```

