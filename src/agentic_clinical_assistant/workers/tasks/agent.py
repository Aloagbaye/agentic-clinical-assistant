"""Agent workflow tasks."""

import uuid
from typing import Any, Dict, Optional

from celery import Task
from celery.exceptions import Retry

from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database.models.agent_run import RunStatus
from agentic_clinical_assistant.workers.celery_app import celery_app


class AgentTask(Task):
    """Base task class for agent operations with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        run_id = kwargs.get("run_id") or (args[0] if args else None)
        if run_id:
            # Update run status to failed
            # This would need to be done in an async context
            pass


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.agent.run_agent_workflow",
    base=AgentTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_agent_workflow(self, run_id: uuid.UUID, request_text: str, user_id: Optional[str] = None):
    """
    Main agent workflow task.

    This task orchestrates the full agent workflow:
    1. Intake Agent
    2. Retrieval Agent
    3. Synthesis Agent
    4. Verifier Agent

    Args:
        run_id: Agent run ID
        request_text: User's request
        user_id: Optional user identifier
    """
    try:
        # Step 1: Intake Agent
        intake_result = run_intake_agent.delay(run_id, request_text).get()

        # Step 2: Retrieval Agent
        retrieval_result = run_retrieval_agent.delay(
            run_id, request_text, intake_result.get("filters", {})
        ).get()

        # Step 3: Synthesis Agent
        synthesis_result = run_synthesis_agent.delay(
            run_id, request_text, retrieval_result.get("evidence", [])
        ).get()

        # Step 4: Verifier Agent
        verifier_result = run_verifier_agent.delay(
            run_id, synthesis_result.get("draft_answer", "")
        ).get()

        # Update final status
        # TODO: Update run status based on verifier result

    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.agent.run_intake_agent",
    bind=True,
    max_retries=2,
)
def run_intake_agent(self, run_id: uuid.UUID, request_text: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Intake Agent task - Classify request and assess risk.

    Args:
        run_id: Agent run ID
        request_text: User's request
        user_id: Optional user identifier

    Returns:
        Request plan with classification and risk assessment
    """
    import asyncio
    from agentic_clinical_assistant.agents.intake.agent import IntakeAgent

    # Create intake agent
    agent = IntakeAgent()
    
    # Get session ID from user_id if available
    session_id = None
    if user_id:
        from agentic_clinical_assistant.memory.session import get_session_memory
        session_memory = get_session_memory()
        loop_temp = asyncio.new_event_loop()
        asyncio.set_event_loop(loop_temp)
        try:
            session = loop_temp.run_until_complete(session_memory.get_user_session(user_id))
            if session:
                session_id = session.session_id
        finally:
            loop_temp.close()
    
    # Run async classification
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        plan = loop.run_until_complete(agent.classify_request(request_text, user_id=user_id, session_id=session_id))
        return plan.to_dict()
    finally:
        loop.close()


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.agent.run_retrieval_agent",
    bind=True,
    max_retries=2,
)
def run_retrieval_agent(
    self, run_id: uuid.UUID, query: str, filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Retrieval Agent task - Find relevant evidence.

    Args:
        run_id: Agent run ID
        query: Search query
        filters: Metadata filters

    Returns:
        Evidence retrieval results
    """
    import asyncio
    from agentic_clinical_assistant.agents.retrieval.agent import RetrievalAgent

    # Create retrieval agent
    agent = RetrievalAgent()
    
    # Run async retrieval
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.retrieve_evidence(query, filters=filters))
        return result.dict()
    finally:
        loop.close()


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.agent.run_synthesis_agent",
    bind=True,
    max_retries=2,
)
def run_synthesis_agent(
    self, run_id: uuid.UUID, request_text: str, evidence: list
) -> Dict[str, Any]:
    """
    Synthesis Agent task - Generate draft answer.

    Args:
        run_id: Agent run ID
        request_text: User's request
        evidence: Retrieved evidence

    Returns:
        Draft answer with citations
    """
    import asyncio
    from agentic_clinical_assistant.agents.synthesis.agent import SynthesisAgent

    # Create synthesis agent
    agent = SynthesisAgent()
    
    # Run async synthesis
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.generate_answer(request_text, evidence))
        return result.dict()
    finally:
        loop.close()


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.agent.run_verifier_agent",
    bind=True,
    max_retries=2,
)
def run_verifier_agent(
    self, run_id: uuid.UUID, draft_answer: str, citations: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Verifier Agent task - Verify safety and grounding.

    Args:
        run_id: Agent run ID
        draft_answer: Draft answer to verify
        citations: Citations for the answer

    Returns:
        Verification result
    """
    import asyncio
    from agentic_clinical_assistant.agents.verifier.agent import VerifierAgent

    # Create verifier agent
    agent = VerifierAgent()
    
    # Run async verification
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.verify(draft_answer, citations))
        return result.dict()
    finally:
        loop.close()

