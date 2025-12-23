# Testing Agents in Python

## The Problem

When you try to use `await` directly in a Python REPL, you get a `SyntaxError`:

```python
>>> await some_async_function()
SyntaxError: 'await' outside function
```

This happens because `await` can only be used inside an `async` function, not at the top level of a script or REPL.

## Quick Solution: Use the Interactive Helper

The easiest way to test agents in the REPL:

```python
# In Python REPL
>>> exec(open('scripts/interactive_agent_test.py').read())
>>> result = test_retrieval("sepsis treatment protocol")
>>> print(result)
```

This loads helper functions that handle async/await for you!

## Solutions

### Option 1: Use `asyncio.run()` (Recommended)

Wrap your async code in a function and use `asyncio.run()`:

```python
import asyncio
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

async def test():
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(
        query="sepsis treatment protocol",
        top_k=10,
        filters={"department": "ER"}
    )
    print(result)
    return result

# Run the async function
result = asyncio.run(test())
```

### Option 2: Use the Test Script

Use the provided test script:

```bash
python scripts/test_agents.py
```

This script tests all agents and shows their results.

### Option 3: Use IPython with Auto-Await

If you have IPython installed, it supports top-level await:

```bash
pip install ipython
ipython
```

Then in IPython:

```python
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

agent = RetrievalAgent()
result = await agent.retrieve_evidence(
    query="sepsis treatment protocol",
    top_k=10
)
print(result)
```

### Option 4: Use Python's Async REPL (Python 3.8+)

Python 3.8+ has an async REPL:

```bash
python -m asyncio
```

Then you can use `await` directly:

```python
>>> from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent
>>> agent = RetrievalAgent()
>>> result = await agent.retrieve_evidence(query="test", top_k=5)
>>> result
```

## Viewing Results

### Printing Results

```python
import asyncio
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

async def test():
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(
        query="sepsis treatment protocol",
        top_k=10
    )
    
    # Print the result object
    print(result)
    
    # Print specific fields
    print(f"Evidence count: {len(result.evidence)}")
    print(f"Backends: {result.backends_queried}")
    
    # Print evidence items
    for item in result.evidence:
        print(f"  - {item.document_id}: {item.score:.2f}")
    
    return result

result = asyncio.run(test())
```

### Converting to Dictionary

All Pydantic models can be converted to dictionaries:

```python
import asyncio
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

async def test():
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(query="test", top_k=5)
    
    # Convert to dict
    result_dict = result.dict()
    print(result_dict)
    
    # Or use model_dump (Pydantic v2)
    result_dict = result.model_dump()
    print(result_dict)
    
    return result_dict

result = asyncio.run(test())
```

### Pretty Printing JSON

```python
import asyncio
import json
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

async def test():
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(query="test", top_k=5)
    
    # Convert to JSON string
    result_json = result.model_dump_json(indent=2)
    print(result_json)
    
    return result

result = asyncio.run(test())
```

## Interactive Testing Examples

### Test Intake Agent

```python
import asyncio
from agentic_clinical_assistant.agents.intake.agent import IntakeAgent

async def test_intake():
    agent = IntakeAgent()
    plan = await agent.classify_request("What is the policy for sepsis treatment?")
    
    print(f"Type: {plan.request_type.value}")
    print(f"Risk: {plan.risk_label.value}")
    print(f"Tools: {plan.required_tools}")
    print(f"Constraints: {plan.constraints}")
    
    return plan

plan = asyncio.run(test_intake())
```

### Test Retrieval Agent

```python
import asyncio
from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

async def test_retrieval():
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(
        query="sepsis treatment protocol",
        top_k=10,
        filters={"department": "ER"}
    )
    
    print(f"Found {len(result.evidence)} evidence items")
    for item in result.evidence:
        print(f"  - {item.document_id}: score={item.score:.2f}")
    
    return result

result = asyncio.run(test_retrieval())
```

### Test Synthesis Agent

```python
import asyncio
from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent

async def test_synthesis():
    # Mock evidence
    evidence = [
        {
            "document_id": "doc1",
            "text": "Sepsis treatment requires immediate antibiotics...",
            "score": 0.95,
            "doc_hash": "hash1"
        }
    ]
    
    agent = SynthesisAgent()
    result = await agent.generate_answer(
        request_text="What is the policy for sepsis?",
        evidence=evidence
    )
    
    print(f"Answer: {result.draft_answer}")
    print(f"Citations: {len(result.citations)}")
    
    return result

result = asyncio.run(test_synthesis())
```

### Test Verifier Agent

```python
import asyncio
from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent

async def test_verifier():
    agent = VerifierAgent()
    
    result = await agent.verify(
        draft_answer="According to the policy, sepsis requires antibiotics.",
        citations=[{"document_id": "doc1", "doc_hash": "hash1"}]
    )
    
    print(f"Passed: {result.passed}")
    print(f"PHI Detected: {result.phi_detected}")
    print(f"Grounding Score: {result.grounding_score:.2f}")
    
    if result.issues:
        print("Issues:")
        for issue in result.issues:
            print(f"  - {issue.issue_type}: {issue.description}")
    
    return result

result = asyncio.run(test_verifier())
```

## Quick Reference

**Always use `asyncio.run()` for top-level async code:**

```python
import asyncio

async def my_test():
    # Your async code here
    result = await some_async_function()
    return result

# Run it
result = asyncio.run(my_test())
```

**Or use the test script:**

```bash
python scripts/test_agents.py
```

