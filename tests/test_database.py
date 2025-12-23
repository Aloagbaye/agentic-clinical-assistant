"""Tests for database models and audit logging."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database.base import Base
from agentic_clinical_assistant.database.models.agent_run import RunStatus


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_audit_logger_agent_run(db_session: AsyncSession):
    """Test logging agent run."""
    audit = AuditLogger(db_session)
    
    run_id = await audit.log_agent_run(
        request_text="Test request",
        user_id="test_user",
        request_type="policy_lookup",
        risk_label="low",
    )
    
    assert run_id is not None
    
    # Verify run was created
    from agentic_clinical_assistant.database.models.agent_run import AgentRun
    
    run = await db_session.get(AgentRun, run_id)
    assert run is not None
    assert run.request_text == "Test request"
    assert run.user_id == "test_user"
    assert run.status == RunStatus.PENDING


@pytest.mark.asyncio
async def test_audit_logger_tool_call(db_session: AsyncSession):
    """Test logging tool call."""
    audit = AuditLogger(db_session)
    
    # First create an agent run
    run_id = await audit.log_agent_run(request_text="Test")
    
    # Log tool call
    tool_call_id = await audit.log_tool_call(
        run_id=run_id,
        tool_name="retrieve_evidence",
        inputs={"query": "test", "backend": "faiss"},
        backend="faiss",
        duration_ms=100.5,
    )
    
    assert tool_call_id is not None
    
    # Verify tool call was created
    from agentic_clinical_assistant.database.models.tool_call import ToolCall
    
    tool_call = await db_session.get(ToolCall, tool_call_id)
    assert tool_call is not None
    assert tool_call.tool_name == "retrieve_evidence"
    assert tool_call.backend == "faiss"
    assert tool_call.duration_ms == 100.5
    assert tool_call.success == "true"


@pytest.mark.asyncio
async def test_audit_logger_evidence_retrieval(db_session: AsyncSession):
    """Test logging evidence retrieval."""
    audit = AuditLogger(db_session)
    
    # Create agent run
    run_id = await audit.log_agent_run(request_text="Test")
    
    # Log evidence retrieval
    retrieval_id = await audit.log_evidence_retrieval(
        run_id=run_id,
        query="test query",
        backend="faiss",
        doc_hashes=["hash1", "hash2", "hash3"],
        top_k=10,
        scores=[0.95, 0.87, 0.82],
    )
    
    assert retrieval_id is not None
    
    # Verify retrieval was created
    from agentic_clinical_assistant.database.models.evidence_retrieval import (
        EvidenceRetrieval,
    )
    
    retrieval = await db_session.get(EvidenceRetrieval, retrieval_id)
    assert retrieval is not None
    assert retrieval.query == "test query"
    assert retrieval.backend == "faiss"
    assert retrieval.result_count == 3
    assert len(retrieval.doc_hashes) == 3


@pytest.mark.asyncio
async def test_audit_logger_citation(db_session: AsyncSession):
    """Test logging citation."""
    audit = AuditLogger(db_session)
    
    # Create agent run
    run_id = await audit.log_agent_run(request_text="Test")
    
    # Log citation
    citation_id = await audit.log_citation(
        run_id=run_id,
        claim_text="Policy X states that...",
        doc_hash="abc123def456",
        doc_title="Policy Document X",
        relevance_score="0.95",
    )
    
    assert citation_id is not None
    
    # Verify citation was created
    from agentic_clinical_assistant.database.models.citation import Citation
    
    citation = await db_session.get(Citation, citation_id)
    assert citation is not None
    assert citation.claim_text == "Policy X states that..."
    assert citation.doc_hash == "abc123def456"
    assert citation.doc_title == "Policy Document X"


@pytest.mark.asyncio
async def test_audit_logger_grounding_verification(db_session: AsyncSession):
    """Test logging grounding verification."""
    audit = AuditLogger(db_session)
    
    # Create agent run
    run_id = await audit.log_agent_run(request_text="Test")
    
    # Log grounding verification
    verification_id = await audit.log_grounding_verification(
        run_id=run_id,
        status="pass",
        passed=True,
        total_claims=5,
        grounded_claims=5,
        phi_redaction_count=2,
    )
    
    assert verification_id is not None
    
    # Verify verification was created
    from agentic_clinical_assistant.database.models.grounding_verification import (
        GroundingVerification,
    )
    
    verification = await db_session.get(GroundingVerification, verification_id)
    assert verification is not None
    assert verification.status == "pass"
    assert verification.passed == "true"
    assert verification.total_claims == "5"
    assert verification.grounded_claims == "5"

