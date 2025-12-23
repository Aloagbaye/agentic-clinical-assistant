"""Celery task workers for core tools."""

import asyncio
from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.tools.core import (
    generate_answer,
    redact_phi,
    retrieve_evidence,
    run_backend_benchmark,
    verify_grounding,
)
from agentic_clinical_assistant.workers.celery_app import celery_app


@celery_app.task(name="agentic_clinical_assistant.tools.workers.core.tool_retrieve_evidence")
def tool_retrieve_evidence(
    query: str,
    backend: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for retrieve_evidence tool.

    Args:
        query: Search query
        backend: Backend to use
        filters: Metadata filters
        top_k: Number of results
        run_id: Agent run ID

    Returns:
        Evidence retrieval results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            retrieve_evidence(query=query, backend=backend, filters=filters, top_k=top_k, run_id=run_id)
        )
    finally:
        loop.close()


@celery_app.task(name="agentic_clinical_assistant.tools.workers.core.tool_redact_phi")
def tool_redact_phi(
    text: str,
    run_id: Optional[str] = None,
    aggressive: bool = False,
) -> Dict[str, Any]:
    """
    Celery task wrapper for redact_phi tool.

    Args:
        text: Text to redact
        run_id: Agent run ID
        aggressive: Aggressive redaction mode

    Returns:
        Redaction results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(redact_phi(text=text, run_id=run_id, aggressive=aggressive))
    finally:
        loop.close()


@celery_app.task(name="agentic_clinical_assistant.tools.workers.core.tool_run_backend_benchmark")
def tool_run_backend_benchmark(
    eval_set_id: str,
    backends: Optional[List[str]] = None,
    benchmark_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for run_backend_benchmark tool.

    Args:
        eval_set_id: Evaluation dataset ID
        backends: Backends to evaluate
        benchmark_id: Benchmark run ID
        run_id: Agent run ID

    Returns:
        Benchmark results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            run_backend_benchmark(
                eval_set_id=eval_set_id, backends=backends, benchmark_id=benchmark_id, run_id=run_id
            )
        )
    finally:
        loop.close()


@celery_app.task(name="agentic_clinical_assistant.tools.workers.core.tool_generate_answer")
def tool_generate_answer(
    evidence_bundle: List[Dict[str, Any]],
    request_text: str,
    prompt_version: Optional[str] = None,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for generate_answer tool.

    Args:
        evidence_bundle: Evidence items
        request_text: User request
        prompt_version: Prompt version
        model: LLM model
        run_id: Agent run ID

    Returns:
        Generated answer
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            generate_answer(
                evidence_bundle=evidence_bundle,
                request_text=request_text,
                prompt_version=prompt_version,
                model=model,
                run_id=run_id,
            )
        )
    finally:
        loop.close()


@celery_app.task(name="agentic_clinical_assistant.tools.workers.core.tool_verify_grounding")
def tool_verify_grounding(
    draft_answer: str,
    evidence_bundle: List[Dict[str, Any]],
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task wrapper for verify_grounding tool.

    Args:
        draft_answer: Draft answer
        evidence_bundle: Evidence items
        run_id: Agent run ID

    Returns:
        Verification results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            verify_grounding(draft_answer=draft_answer, evidence_bundle=evidence_bundle, run_id=run_id)
        )
    finally:
        loop.close()

