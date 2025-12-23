"""Audit logging utilities for tracking all system operations."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from agentic_clinical_assistant.database.models.agent_run import AgentRun, RunStatus
from agentic_clinical_assistant.database.models.citation import Citation
from agentic_clinical_assistant.database.models.evidence_retrieval import EvidenceRetrieval
from agentic_clinical_assistant.database.models.grounding_verification import (
    GroundingVerification,
)
from agentic_clinical_assistant.database.models.tool_call import ToolCall


class AuditLogger:
    """Audit logging service for tracking agent operations."""

    def __init__(self, session: AsyncSession):
        """Initialize audit logger with database session."""
        self.session = session

    async def log_agent_run(
        self,
        request_text: str,
        user_id: Optional[str] = None,
        request_type: Optional[str] = None,
        risk_label: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """
        Log the start of an agent run.

        Args:
            request_text: The user's request text
            user_id: Optional user identifier
            request_type: Type of request (e.g., "policy_lookup")
            risk_label: Risk classification (e.g., "low", "medium", "high")
            metadata: Additional metadata

        Returns:
            UUID of the created agent run
        """
        run = AgentRun(
            run_id=uuid.uuid4(),
            status=RunStatus.PENDING,
            user_id=user_id,
            request_text=request_text,
            request_type=request_type,
            risk_label=risk_label,
            extra_metadata=extra_metadata,
            created_at=datetime.utcnow(),
        )
        self.session.add(run)
        await self.session.flush()
        return run.run_id

    async def update_agent_run_status(
        self,
        run_id: uuid.UUID,
        status: RunStatus,
        final_answer: Optional[str] = None,
        abstention_reason: Optional[str] = None,
    ) -> None:
        """
        Update agent run status.

        Args:
            run_id: UUID of the agent run
            status: New status
            final_answer: Final answer if completed
            abstention_reason: Reason if abstained
        """
        run = await self.session.get(AgentRun, run_id)
        if run:
            run.status = status
            if status == RunStatus.RUNNING and not run.started_at:
                run.started_at = datetime.utcnow()
            if status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABSTAINED):
                run.completed_at = datetime.utcnow()
            if final_answer:
                run.final_answer = final_answer
            if abstention_reason:
                run.abstention_reason = abstention_reason
            await self.session.flush()

    async def log_tool_call(
        self,
        run_id: uuid.UUID,
        tool_name: str,
        inputs: Dict[str, Any],
        backend: Optional[str] = None,
        outputs: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """
        Log a tool call.

        Args:
            run_id: UUID of the agent run
            tool_name: Name of the tool
            inputs: Tool input parameters
            backend: Backend used (if applicable)
            outputs: Tool output results
            duration_ms: Duration in milliseconds
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            UUID of the created tool call record
        """
        tool_call = ToolCall(
            tool_call_id=uuid.uuid4(),
            run_id=run_id,
            tool_name=tool_name,
            backend=backend,
            inputs=inputs,
            outputs=outputs,
            duration_ms=duration_ms,
            error_message=error_message,
            success="false" if error_message else "true",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if duration_ms else None,
            extra_metadata=extra_metadata,
        )
        self.session.add(tool_call)
        await self.session.flush()
        return tool_call.tool_call_id

    async def log_evidence_retrieval(
        self,
        run_id: uuid.UUID,
        query: str,
        backend: str,
        doc_hashes: list[str],
        top_k: int = 10,
        scores: Optional[list[float]] = None,
        retrieval_mode: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        tool_call_id: Optional[uuid.UUID] = None,
        duration_ms: Optional[float] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """
        Log evidence retrieval operation.

        Args:
            run_id: UUID of the agent run
            query: Search query
            backend: Vector backend used
            doc_hashes: List of document hashes retrieved
            top_k: Number of results requested
            scores: Similarity scores
            retrieval_mode: Retrieval mode (vector/hybrid/keyword)
            filters: Metadata filters applied
            tool_call_id: Optional tool call ID
            duration_ms: Duration in milliseconds
            metadata: Additional metadata

        Returns:
            UUID of the created evidence retrieval record
        """
        retrieval = EvidenceRetrieval(
            retrieval_id=uuid.uuid4(),
            run_id=run_id,
            tool_call_id=tool_call_id,
            query=query,
            backend=backend,
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            filters=filters,
            result_count=len(doc_hashes),
            scores=scores,
            doc_hashes=doc_hashes,
            duration_ms=duration_ms,
            retrieved_at=datetime.utcnow(),
            extra_metadata=extra_metadata,
        )
        self.session.add(retrieval)
        await self.session.flush()
        return retrieval.retrieval_id

    async def log_citation(
        self,
        run_id: uuid.UUID,
        claim_text: str,
        doc_hash: str,
        doc_title: Optional[str] = None,
        doc_section: Optional[str] = None,
        doc_url: Optional[str] = None,
        retrieval_id: Optional[uuid.UUID] = None,
        relevance_score: Optional[str] = None,
        claim_position: Optional[int] = None,
    ) -> uuid.UUID:
        """
        Log a citation mapping claim to source.

        Args:
            run_id: UUID of the agent run
            claim_text: The claim being cited
            doc_hash: SHA-256 hash of source document
            doc_title: Document title
            doc_section: Section reference
            doc_url: Optional URL to source
            retrieval_id: Optional evidence retrieval ID
            relevance_score: Similarity score
            claim_position: Position in answer

        Returns:
            UUID of the created citation record
        """
        citation = Citation(
            citation_id=uuid.uuid4(),
            run_id=run_id,
            claim_text=claim_text,
            claim_position=claim_position,
            doc_hash=doc_hash,
            doc_title=doc_title,
            doc_section=doc_section,
            doc_url=doc_url,
            retrieval_id=retrieval_id,
            relevance_score=relevance_score,
            created_at=datetime.utcnow(),
        )
        self.session.add(citation)
        await self.session.flush()
        return citation.citation_id

    async def log_grounding_verification(
        self,
        run_id: uuid.UUID,
        status: str,
        passed: bool,
        total_claims: int,
        grounded_claims: int,
        ungrounded_claims: Optional[list[str]] = None,
        issues: Optional[list[str]] = None,
        phi_redaction_count: int = 0,
        prompt_injection_detected: bool = False,
        verification_reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """
        Log grounding verification result.

        Args:
            run_id: UUID of the agent run
            status: Verification status ("pass", "fail", "partial")
            passed: Whether verification passed
            total_claims: Total number of claims checked
            grounded_claims: Number of claims with citations
            ungrounded_claims: List of ungrounded claims
            issues: List of issues found
            phi_redaction_count: Number of PHI redactions
            prompt_injection_detected: Whether prompt injection was detected
            verification_reason: Explanation of result
            metadata: Additional metadata

        Returns:
            UUID of the created verification record
        """
        verification = GroundingVerification(
            verification_id=uuid.uuid4(),
            run_id=run_id,
            status=status,
            passed="true" if passed else "false",
            total_claims=str(total_claims),
            grounded_claims=str(grounded_claims),
            ungrounded_claims=ungrounded_claims,
            issues=issues,
            phi_redaction_count=str(phi_redaction_count),
            prompt_injection_detected="true" if prompt_injection_detected else "false",
            verification_reason=verification_reason,
            verified_at=datetime.utcnow(),
            extra_metadata=extra_metadata,
        )
        self.session.add(verification)
        await self.session.flush()
        return verification.verification_id

