"""Script to test agents interactively."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_intake_agent():
    """Test Intake Agent."""
    from agentic_clinical_assistant.agents.intake.agent import IntakeAgent
    
    agent = IntakeAgent()
    plan = await agent.classify_request("What is the policy for sepsis treatment?")
    
    print("=== Intake Agent Result ===")
    print(f"Request Type: {plan.request_type.value}")
    print(f"Risk Label: {plan.risk_label.value}")
    print(f"Required Tools: {plan.required_tools}")
    print(f"Constraints: {plan.constraints}")
    print(f"Confidence: {plan.confidence:.2f}")
    print()


async def test_retrieval_agent():
    """Test Retrieval Agent."""
    from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent
    
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(
        query="sepsis treatment protocol",
        top_k=10,
        filters={"department": "ER"}
    )
    
    print("=== Retrieval Agent Result ===")
    print(f"Evidence Count: {len(result.evidence)}")
    print(f"Backends Queried: {result.metadata.get('backends_queried', [])}")
    print(f"Selected Backend: {result.backend}")
    print(f"Total Results: {result.metadata.get('total_results', 0)}")
    print()


async def test_synthesis_agent():
    """Test Synthesis Agent."""
    from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent
    
    # Mock evidence
    evidence = [
        {
            "document_id": "doc1",
            "text": "Sepsis treatment requires immediate antibiotic administration...",
            "score": 0.95,
            "doc_hash": "hash1",
            "metadata": {"source": "policy_doc_001"}
        }
    ]
    
    agent = SynthesisAgent()
    result = await agent.generate_answer(
        request_text="What is the policy for sepsis treatment?",
        evidence=evidence
    )
    
    print("=== Synthesis Agent Result ===")
    print(f"Draft Answer: {result.draft_answer[:200]}...")
    print(f"Citations: {len(result.citations)}")
    print(f"Confidence: {result.confidence:.2f}")
    print()


async def test_verifier_agent():
    """Test Verifier Agent."""
    from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent
    
    agent = VerifierAgent()
    
    # Test with clean answer
    result1 = await agent.verify(
        draft_answer="According to the policy, sepsis treatment requires immediate antibiotics.",
        citations=[{"document_id": "doc1", "doc_hash": "hash1"}]
    )
    
    print("=== Verifier Agent Result (Clean) ===")
    print(f"Passed: {result1.passed}")
    print(f"Status: {result1.status}")
    print(f"PHI Detected: {result1.phi_detected}")
    print(f"Grounding Score: {result1.grounding_score:.2f}")
    print()
    
    # Test with PHI
    result2 = await agent.verify(
        draft_answer="Patient SSN: 123-45-6789 was admitted on 01/15/2024",
        citations=[]
    )
    
    print("=== Verifier Agent Result (With PHI) ===")
    print(f"Passed: {result2.passed}")
    print(f"PHI Detected: {result2.phi_detected}")
    print(f"PHI Count: {result2.phi_count}")
    print(f"Issues: {len(result2.issues)}")
    for issue in result2.issues:
        print(f"  - {issue.issue_type}: {issue.description}")
    print()


async def main():
    """Run all agent tests."""
    print("Testing Specialized Agents\n")
    print("=" * 50)
    print()
    
    await test_intake_agent()
    await test_retrieval_agent()
    await test_synthesis_agent()
    await test_verifier_agent()
    
    print("=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())

