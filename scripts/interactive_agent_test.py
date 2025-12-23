"""Interactive helper for testing agents in Python REPL.

Usage in Python REPL:
    >>> exec(open('scripts/interactive_agent_test.py').read())
    >>> result = test_retrieval("sepsis treatment")
    >>> print(result)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _run_async(coro):
    """Helper to run async functions synchronously."""
    return asyncio.run(coro)


def test_intake(request_text: str):
    """Test Intake Agent.
    
    Example:
        >>> plan = test_intake("What is the policy for sepsis?")
        >>> print(plan.request_type.value)
    """
    from agentic_clinical_assistant.agents.intake.agent import IntakeAgent
    
    agent = IntakeAgent()
    return _run_async(agent.classify_request(request_text))


def test_retrieval(query: str, top_k: int = 10, filters: dict = None):
    """Test Retrieval Agent.
    
    Example:
        >>> result = test_retrieval("sepsis treatment", top_k=5)
        >>> print(f"Found {len(result.evidence)} results")
    """
    from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent
    
    agent = RetrievalAgent()
    return _run_async(agent.retrieve_evidence(query, top_k=top_k, filters=filters or {}))


def test_synthesis(request_text: str, evidence: list = None):
    """Test Synthesis Agent.
    
    Example:
        >>> evidence = [{"text": "Policy says...", "score": 0.9, "doc_hash": "hash1"}]
        >>> result = test_synthesis("What is the policy?", evidence)
        >>> print(result.draft_answer)
    """
    from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent
    
    if evidence is None:
        evidence = [
            {
                "document_id": "doc1",
                "text": "Sample policy text for testing...",
                "score": 0.9,
                "doc_hash": "hash1",
                "metadata": {}
            }
        ]
    
    agent = SynthesisAgent()
    return _run_async(agent.generate_answer(request_text, evidence))


def test_verifier(draft_answer: str, citations: list = None):
    """Test Verifier Agent.
    
    Example:
        >>> result = test_verifier("According to policy, sepsis requires antibiotics.")
        >>> print(f"Passed: {result.passed}")
    """
    from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent
    
    if citations is None:
        citations = []
    
    agent = VerifierAgent()
    return _run_async(agent.verify(draft_answer, citations))


# Print help message
print("=" * 60)
print("Agent Testing Helper Functions Loaded!")
print("=" * 60)
print()
print("Available functions:")
print("  - test_intake(request_text)")
print("  - test_retrieval(query, top_k=10, filters=None)")
print("  - test_synthesis(request_text, evidence=None)")
print("  - test_verifier(draft_answer, citations=None)")
print()
print("Example:")
print("  >>> plan = test_intake('What is the policy for sepsis?')")
print("  >>> print(plan.request_type.value)")
print()
print("=" * 60)

