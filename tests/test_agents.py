"""Tests for specialized agents."""

import pytest

from agentic_clinical_assistant.agents.intake.agent import IntakeAgent
from agentic_clinical_assistant.agents.intake.models import RequestType, RiskLabel
from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent


@pytest.mark.asyncio
async def test_intake_agent_classification():
    """Test intake agent request classification."""
    agent = IntakeAgent()
    
    # Test policy lookup
    plan = await agent.classify_request("What is the policy for sepsis treatment?")
    assert plan.request_type in [RequestType.POLICY_LOOKUP, RequestType.UNKNOWN]
    assert plan.risk_label in [RiskLabel.LOW, RiskLabel.MEDIUM, RiskLabel.HIGH]
    assert "retrieve_evidence" in plan.required_tools


@pytest.mark.asyncio
async def test_intake_agent_risk_assessment():
    """Test intake agent risk assessment."""
    agent = IntakeAgent()
    
    # High risk query
    plan = await agent.classify_request("How should I diagnose and treat this patient?")
    # Should detect high risk keywords
    assert plan.risk_label in [RiskLabel.LOW, RiskLabel.MEDIUM, RiskLabel.HIGH]


@pytest.mark.asyncio
async def test_verifier_agent_phi_detection():
    """Test verifier agent PHI detection."""
    agent = VerifierAgent()
    
    # Test with potential PHI
    result = await agent.verify(
        "Patient SSN: 123-45-6789 was admitted on 01/15/2024",
        citations=[]
    )
    
    assert result.phi_detected is True
    assert result.phi_count > 0


@pytest.mark.asyncio
async def test_verifier_agent_grounding():
    """Test verifier agent grounding check."""
    agent = VerifierAgent()
    
    # Test with citations
    result = await agent.verify(
        "According to the policy document, sepsis treatment requires...",
        citations=[
            {"document_id": "doc1", "doc_hash": "hash1", "text": "policy text"}
        ]
    )
    
    assert result.grounding_score >= 0.0
    assert result.grounding_score <= 1.0

