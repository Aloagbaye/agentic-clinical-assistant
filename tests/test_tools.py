"""Tests for core tools."""

import pytest

from agentic_clinical_assistant.tools.core import compute_doc_hash, redact_phi
from agentic_clinical_assistant.tools.registry import get_registry


@pytest.mark.asyncio
async def test_redact_phi():
    """Test PHI redaction tool."""
    text = "Patient SSN: 123-45-6789 was admitted on 01/15/2024"
    
    result = await redact_phi(text)
    
    assert result["phi_detected"] is True
    assert result["redaction_count"] > 0
    assert "[SSN]" in result["redacted_text"] or "[ID]" in result["redacted_text"]
    assert "123-45-6789" not in result["redacted_text"]


@pytest.mark.asyncio
async def test_redact_phi_no_phi():
    """Test PHI redaction with no PHI."""
    text = "This is a normal policy document with no sensitive information."
    
    result = await redact_phi(text)
    
    assert result["phi_detected"] is False
    assert result["redaction_count"] == 0


def test_compute_doc_hash():
    """Test document hash computation."""
    text = "Test document text"
    hash1 = compute_doc_hash(text)
    hash2 = compute_doc_hash(text)
    
    # Same text should produce same hash
    assert hash1 == hash2
    
    # Different text should produce different hash
    hash3 = compute_doc_hash("Different text")
    assert hash1 != hash3


def test_tool_registry():
    """Test tool registry."""
    registry = get_registry()
    
    # List tools
    tools = registry.list_tools()
    assert len(tools) > 0
    
    # Get specific tool
    tool = registry.get_tool("retrieve_evidence")
    assert tool is not None
    assert tool["name"] == "retrieve_evidence"
    
    # Get non-existent tool
    tool = registry.get_tool("nonexistent_tool")
    assert tool is None

