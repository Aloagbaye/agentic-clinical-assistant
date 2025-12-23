"""Core tools for agent operations."""

import hashlib
import re
import time
from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent
from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent
from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent
from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.metrics.collector import MetricsCollector
from agentic_clinical_assistant.vector.base import VectorDBBackend
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator


async def retrieve_evidence(
    query: str,
    backend: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve evidence from vector database.

    Args:
        query: Search query
        backend: Specific backend to use (None = auto-select)
        filters: Metadata filters
        top_k: Number of results to retrieve
        run_id: Agent run ID for logging

    Returns:
        Dictionary with evidence results
    """
    # Record tool call start time
    start_time = time.time()
    
    agent = RetrievalAgent()
    result = await agent.retrieve_evidence(
        query=query,
        top_k=top_k,
        filters=filters or {},
        backends=[backend] if backend else None,
    )
    
    # Record metrics
    latency_ms = (time.time() - start_time) * 1000
    backend_used = result.backend or backend or "unknown"
    MetricsCollector.record_tool_call("retrieve_evidence", backend_used, latency_ms)
    
    # Record retrieval latency if backend is known
    if backend_used != "unknown":
        MetricsCollector.record_retrieval_metrics(backend_used, latency_ms=latency_ms)

    # Log tool call
    if run_id:
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.log_tool_call(
                run_id=run_id,
                tool_name="retrieve_evidence",
                tool_input={"query": query, "backend": backend, "filters": filters, "top_k": top_k},
                tool_output={"evidence_count": len(result.evidence)},
            )
            await session.commit()

    return result.dict()


async def redact_phi(
    text: str,
    run_id: Optional[str] = None,
    aggressive: bool = False,
) -> Dict[str, Any]:
    """
    Redact PHI/PII from text.

    Args:
        text: Text to redact
        run_id: Agent run ID for logging
        aggressive: Use aggressive redaction (more patterns)

    Returns:
        Dictionary with redacted text and redaction details
    """
    # PHI/PII patterns
    patterns = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),  # SSN
        (r"\b\d{3}\.\d{2}\.\d{4}\b", "[SSN]"),  # SSN with dots
        (r"\b\d{10}\b", "[ID]"),  # 10-digit number
        (r"\b[A-Z]{2}\d{6}\b", "[MRN]"),  # Medical record number
        (r"\b\d{4}-\d{2}-\d{2}\b", "[DATE]"),  # Date
        (r"\b\d{1,2}/\d{1,2}/\d{4}\b", "[DATE]"),  # Date format
        (r"\b\d{3}-\d{3}-\d{4}\b", "[PHONE]"),  # Phone number
        (r"\b\d{3}\.\d{3}\.\d{4}\b", "[PHONE]"),  # Phone with dots
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),  # Email
    ]

    if aggressive:
        # Additional aggressive patterns
        patterns.extend([
            (r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", "[NAME]"),  # Name pattern (simple)
            (r"\b\d{1,3}\s+[A-Z][a-z]+\s+St(?:reet|\.)?\b", "[ADDRESS]"),  # Street address
        ])

    # Record tool call start time
    start_time = time.time()
    
    redacted_text = text
    redactions = []
    total_count = 0

    for pattern, replacement in patterns:
        matches = list(re.finditer(pattern, redacted_text, re.IGNORECASE))
        if matches:
            # Replace in reverse order to maintain positions
            for match in reversed(matches):
                redacted_text = (
                    redacted_text[: match.start()] + replacement + redacted_text[match.end() :]
                )
                redactions.append({
                    "pattern": pattern,
                    "replacement": replacement,
                    "position": match.start(),
                    "original": match.group(),
                })
                total_count += 1
                
                # Record PHI redaction by type
                if replacement == "[SSN]":
                    MetricsCollector.record_phi_redaction("ssn")
                elif replacement == "[PHONE]":
                    MetricsCollector.record_phi_redaction("phone")
                elif replacement == "[EMAIL]":
                    MetricsCollector.record_phi_redaction("email")
                elif replacement == "[DATE]":
                    MetricsCollector.record_phi_redaction("date")
                elif replacement == "[NAME]":
                    MetricsCollector.record_phi_redaction("name")
                elif replacement == "[ADDRESS]":
                    MetricsCollector.record_phi_redaction("address")

    # Record metrics
    latency_ms = (time.time() - start_time) * 1000
    MetricsCollector.record_tool_call("redact_phi", "none", latency_ms)

    # Log tool call
    if run_id:
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.log_tool_call(
                run_id=run_id,
                tool_name="redact_phi",
                tool_input={"text_length": len(text), "aggressive": aggressive},
                tool_output={"redaction_count": total_count},
            )
            await session.commit()

    return {
        "redacted_text": redacted_text,
        "original_text": text,
        "redaction_count": total_count,
        "redactions": redactions,
        "phi_detected": total_count > 0,
    }


async def run_backend_benchmark(
    eval_set_id: str,
    backends: Optional[List[str]] = None,
    benchmark_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run benchmark evaluation on vector backends.

    Args:
        eval_set_id: Evaluation dataset identifier
        backends: List of backends to evaluate (None = all)
        benchmark_id: Benchmark run identifier
        run_id: Agent run ID for logging

    Returns:
        Dictionary with benchmark results
    """
    from agentic_clinical_assistant.workers.tasks.evaluation import run_evaluation

    if backends is None:
        backends = ["faiss", "pinecone", "weaviate"]

    # Dispatch evaluation task
    task = run_evaluation.delay(eval_set_id, backends, benchmark_id)
    results = task.get(timeout=600)  # 10 minute timeout

    # Log tool call
    if run_id:
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.log_tool_call(
                run_id=run_id,
                tool_name="run_backend_benchmark",
                tool_input={"eval_set_id": eval_set_id, "backends": backends},
                tool_output={"benchmark_id": results.get("benchmark_id")},
            )
            await session.commit()

    return results


async def generate_answer(
    evidence_bundle: List[Dict[str, Any]],
    request_text: str,
    prompt_version: Optional[str] = None,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate answer from evidence bundle.

    Args:
        evidence_bundle: List of evidence items
        request_text: Original user request
        prompt_version: Prompt version to use
        model: LLM model to use
        run_id: Agent run ID for logging

    Returns:
        Dictionary with generated answer and citations
    """
    # Record tool call start time
    start_time = time.time()
    
    agent = SynthesisAgent()
    result = await agent.generate_answer(
        request_text=request_text,
        evidence=evidence_bundle,
    )
    
    # Record metrics
    latency_ms = (time.time() - start_time) * 1000
    MetricsCollector.record_tool_call("generate_answer", "none", latency_ms)
    
    # Check for citations
    if not result.citations or len(result.citations) == 0:
        MetricsCollector.record_citationless_answer()

    # Log tool call
    if run_id:
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.log_tool_call(
                run_id=run_id,
                tool_name="generate_answer",
                tool_input={
                    "evidence_count": len(evidence_bundle),
                    "prompt_version": prompt_version,
                    "model": model,
                },
                tool_output={"answer_length": len(result.draft_answer), "citations": len(result.citations)},
            )
            await session.commit()

    return result.dict()


async def verify_grounding(
    draft_answer: str,
    evidence_bundle: List[Dict[str, Any]],
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify grounding of draft answer in evidence.

    Args:
        draft_answer: Draft answer to verify
        evidence_bundle: Evidence used to generate answer
        run_id: Agent run ID for logging

    Returns:
        Dictionary with verification result
    """
    # Extract citations from evidence bundle
    citations = [
        {
            "document_id": item.get("document_id", ""),
            "doc_hash": item.get("doc_hash", ""),
            "text": item.get("text", ""),
            "score": item.get("score", 0.0),
        }
        for item in evidence_bundle
    ]

    # Record tool call start time
    start_time = time.time()
    
    agent = VerifierAgent()
    result = await agent.verify(draft_answer=draft_answer, citations=citations)
    
    # Record metrics
    latency_ms = (time.time() - start_time) * 1000
    MetricsCollector.record_tool_call("verify_grounding", "none", latency_ms)
    
    # Record grounding metrics
    if not result.passed:
        if not citations or len(citations) == 0:
            MetricsCollector.record_grounding_fail("no_citations")
        elif result.grounding_score < 0.5:
            MetricsCollector.record_grounding_fail("weak_grounding")
        else:
            MetricsCollector.record_grounding_fail("citation_mismatch")

    # Log tool call
    if run_id:
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.log_tool_call(
                run_id=run_id,
                tool_name="verify_grounding",
                tool_input={"answer_length": len(draft_answer), "evidence_count": len(evidence_bundle)},
                tool_output={"passed": result.passed, "grounding_score": result.grounding_score},
            )
            await session.commit()

    return result.dict()


def compute_doc_hash(text: str) -> str:
    """
    Compute document hash for deduplication.

    Args:
        text: Document text

    Returns:
        SHA256 hash of document
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

