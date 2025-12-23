# Specialized Agents

This module contains the specialized agents that form the core of the agentic clinical assistant system.

## Agents Overview

### 1. Intake Agent

**Purpose**: Classifies user requests and assesses risk levels.

**Key Features**:
- Request type classification (policy lookup, summarize, compare, explain)
- Risk assessment (low/medium/high)
- Constraint extraction (department, location, timeframe)
- Required tools determination

**Usage**:
```python
from agentic_clinical_assistant.agents.intake.agent import IntakeAgent

agent = IntakeAgent()
plan = await agent.classify_request("What is the policy for sepsis treatment?")
print(f"Type: {plan.request_type}, Risk: {plan.risk_label}")
```

### 2. Retrieval Agent

**Purpose**: Retrieves relevant evidence from vector databases.

**Key Features**:
- Multi-backend retrieval (FAISS, Pinecone, Weaviate)
- Metadata filtering
- Query expansion
- Evidence bundling

**Usage**:
```python
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

agent = RetrievalAgent()
result = await agent.retrieve_evidence(
    query="sepsis treatment protocol",
    top_k=10,
    filters={"department": "ER"}
)
```

### 3. Synthesis Agent

**Purpose**: Generates draft answers with citations.

**Key Features**:
- Answer generation from evidence
- Citation mapping
- Confidence scoring
- PHI-aware processing

**Usage**:
```python
from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent

agent = SynthesisAgent()
result = await agent.generate_answer(
    request_text="What is the policy?",
    evidence=[...]
)
print(result.draft_answer)
```

### 4. Verifier Agent

**Purpose**: Verifies safety and grounding of answers.

**Key Features**:
- PHI/PII detection
- Prompt injection resistance
- Grounding verification
- Safety checks

**Usage**:
```python
from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent

agent = VerifierAgent()
result = await agent.verify(
    draft_answer="...",
    citations=[...]
)
print(f"Passed: {result.passed}, Issues: {len(result.issues)}")
```

## Agent Workflow

```
User Request
    ↓
Intake Agent → RequestPlan (type, risk, tools)
    ↓
Retrieval Agent → Evidence Bundle
    ↓
Synthesis Agent → Draft Answer + Citations
    ↓
Verifier Agent → Verified Answer or Abstention
```

## Integration

All agents are integrated with:

- **Workflow Engine**: Agents are called by the workflow engine
- **Celery Tasks**: Agents run as Celery tasks for async execution
- **Database**: All agent actions are logged to audit tables
- **Vector DBs**: Retrieval agent queries vector databases

## Future Enhancements

- LLM integration for classification and generation
- Advanced query expansion
- Multi-hop retrieval
- Citation quality scoring
- Advanced PHI detection with NER

