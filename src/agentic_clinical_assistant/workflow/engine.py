"""Workflow engine for orchestrating agent execution."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database.models.agent_run import RunStatus
from agentic_clinical_assistant.workflow.state import (
    StepResult,
    StepStatus,
    WorkflowState,
    WorkflowStatus,
)
from agentic_clinical_assistant.workers.tasks.agent import (
    run_intake_agent,
    run_retrieval_agent,
    run_synthesis_agent,
    run_verifier_agent,
)


class WorkflowEngine:
    """Orchestrates the execution of agent workflows."""

    def __init__(self, run_id: uuid.UUID):
        """
        Initialize workflow engine.

        Args:
            run_id: Agent run identifier
        """
        self.run_id = run_id
        self.state: Optional[WorkflowState] = None

    async def initialize(self, request_text: str, user_id: Optional[str] = None) -> WorkflowState:
        """
        Initialize workflow state.

        Args:
            request_text: User's request
            user_id: Optional user identifier

        Returns:
            Initial workflow state
        """
        self.state = WorkflowState(
            run_id=self.run_id,
            status=WorkflowStatus.PENDING,
            request_text=request_text,
            user_id=user_id,
        )
        return self.state

    async def execute(self) -> WorkflowState:
        """
        Execute the complete workflow.

        Returns:
            Final workflow state
        """
        if self.state is None:
            raise RuntimeError("Workflow not initialized. Call initialize() first.")

        self.state.status = WorkflowStatus.RUNNING
        self.state.started_at = datetime.utcnow()
        self.state.current_step = "intake"

        try:
            # Step 1: Intake Agent
            await self._execute_intake()

            # Step 2: Retrieval Agent
            await self._execute_retrieval()

            # Step 3: Synthesis Agent
            await self._execute_synthesis()

            # Step 4: Verifier Agent
            await self._execute_verification()

            # Finalize workflow
            await self._finalize()

        except Exception as e:
            await self._handle_error(str(e))
            raise

        return self.state

    async def _execute_intake(self) -> None:
        """Execute intake agent step."""
        if self.state is None:
            return

        step_start = datetime.utcnow()
        self.state.status = WorkflowStatus.INTAKE
        self.state.current_step = "intake"

        try:
            # Dispatch intake task
            task_result = run_intake_agent.delay(
                self.run_id,
                self.state.request_text,
            )
            intake_data = task_result.get(timeout=60)

            # Create step result
            self.state.intake_result = StepResult(
                step_name="intake",
                status=StepStatus.COMPLETED,
                result=intake_data,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )

            # Update state with intake results
            if intake_data:
                self.state.metadata["request_type"] = intake_data.get("request_type")
                self.state.metadata["risk_label"] = intake_data.get("risk_label")
                self.state.metadata["required_tools"] = intake_data.get("required_tools", [])

            self.state.steps_completed += 1

            # Log to database
            async for session in get_async_session():
                audit = AuditLogger(session)
                await audit.update_agent_run_status(
                    self.run_id,
                    RunStatus.RUNNING,
                    request_type=intake_data.get("request_type") if intake_data else None,
                    risk_label=intake_data.get("risk_label") if intake_data else None,
                )
                await session.commit()

        except Exception as e:
            self.state.intake_result = StepResult(
                step_name="intake",
                status=StepStatus.FAILED,
                error=str(e),
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )
            raise

    async def _execute_retrieval(self) -> None:
        """Execute retrieval agent step."""
        if self.state is None or self.state.intake_result is None:
            raise RuntimeError("Intake step must complete before retrieval")

        step_start = datetime.utcnow()
        self.state.status = WorkflowStatus.RETRIEVAL
        self.state.current_step = "retrieval"

        try:
            # Get filters from intake result
            filters = self.state.intake_result.result.get("filters", {}) if self.state.intake_result.result else {}

            # Dispatch retrieval task
            task_result = run_retrieval_agent.delay(
                self.run_id,
                self.state.request_text,
                filters,
            )
            retrieval_data = task_result.get(timeout=120)

            # Create step result
            self.state.retrieval_result = StepResult(
                step_name="retrieval",
                status=StepStatus.COMPLETED,
                result=retrieval_data,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )

            self.state.steps_completed += 1

            # Log evidence retrieval
            async for session in get_async_session():
                audit = AuditLogger(session)
                evidence = retrieval_data.get("evidence", []) if retrieval_data else []
                for ev in evidence:
                    await audit.log_evidence_retrieval(
                        run_id=self.run_id,
                        query=self.state.request_text,
                        doc_hash=ev.get("doc_hash", ""),
                        score=ev.get("score", 0.0),
                        backend=ev.get("backend", "unknown"),
                    )
                await session.commit()

        except Exception as e:
            self.state.retrieval_result = StepResult(
                step_name="retrieval",
                status=StepStatus.FAILED,
                error=str(e),
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )
            raise

    async def _execute_synthesis(self) -> None:
        """Execute synthesis agent step."""
        if self.state is None or self.state.retrieval_result is None:
            raise RuntimeError("Retrieval step must complete before synthesis")

        step_start = datetime.utcnow()
        self.state.status = WorkflowStatus.SYNTHESIS
        self.state.current_step = "synthesis"

        try:
            # Get evidence from retrieval result
            evidence = (
                self.state.retrieval_result.result.get("evidence", [])
                if self.state.retrieval_result.result
                else []
            )

            # Dispatch synthesis task
            task_result = run_synthesis_agent.delay(
                self.run_id,
                self.state.request_text,
                evidence,
            )
            synthesis_data = task_result.get(timeout=180)

            # Create step result
            self.state.synthesis_result = StepResult(
                step_name="synthesis",
                status=StepStatus.COMPLETED,
                result=synthesis_data,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )

            self.state.steps_completed += 1

        except Exception as e:
            self.state.synthesis_result = StepResult(
                step_name="synthesis",
                status=StepStatus.FAILED,
                error=str(e),
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )
            raise

    async def _execute_verification(self) -> None:
        """Execute verifier agent step."""
        if self.state is None or self.state.synthesis_result is None:
            raise RuntimeError("Synthesis step must complete before verification")

        step_start = datetime.utcnow()
        self.state.status = WorkflowStatus.VERIFICATION
        self.state.current_step = "verification"

        try:
            # Get draft answer and citations from synthesis result
            draft_answer = (
                self.state.synthesis_result.result.get("draft_answer", "")
                if self.state.synthesis_result.result
                else ""
            )
            citations = (
                self.state.synthesis_result.result.get("citations", [])
                if self.state.synthesis_result.result
                else []
            )

            # Dispatch verifier task
            task_result = run_verifier_agent.delay(
                self.run_id,
                draft_answer,
                citations,
            )
            verification_data = task_result.get(timeout=60)

            # Create step result
            self.state.verification_result = StepResult(
                step_name="verification",
                status=StepStatus.COMPLETED,
                result=verification_data,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )

            self.state.steps_completed += 1

            # Check verification result
            if verification_data and verification_data.get("passed", False):
                # Verification passed
                self.state.final_answer = draft_answer
                self.state.citations = (
                    self.state.synthesis_result.result.get("citations", [])
                    if self.state.synthesis_result.result
                    else []
                )
            else:
                # Verification failed - abstain
                self.state.status = WorkflowStatus.ABSTAINED
                self.state.abstention_reason = verification_data.get("reason", "Verification failed") if verification_data else "Verification failed"

            # Log verification
            async for session in get_async_session():
                audit = AuditLogger(session)
                await audit.log_grounding_verification(
                    run_id=self.run_id,
                    passed=verification_data.get("passed", False) if verification_data else False,
                    issues=verification_data.get("issues", []) if verification_data else [],
                )
                await session.commit()

        except Exception as e:
            self.state.verification_result = StepResult(
                step_name="verification",
                status=StepStatus.FAILED,
                error=str(e),
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )
            raise

    async def _finalize(self) -> None:
        """Finalize workflow execution."""
        if self.state is None:
            return

        self.state.completed_at = datetime.utcnow()

        if self.state.status == WorkflowStatus.ABSTAINED:
            final_status = RunStatus.ABSTAINED
        elif self.state.final_answer:
            self.state.status = WorkflowStatus.COMPLETED
            final_status = RunStatus.COMPLETED
        else:
            self.state.status = WorkflowStatus.FAILED
            final_status = RunStatus.FAILED

        # Update database
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.update_agent_run_status(
                self.run_id,
                final_status,
                final_answer=self.state.final_answer,
                abstention_reason=self.state.abstention_reason,
            )
            await session.commit()

    async def _handle_error(self, error_message: str) -> None:
        """Handle workflow error."""
        if self.state is None:
            return

        self.state.status = WorkflowStatus.FAILED
        self.state.error_message = error_message
        self.state.completed_at = datetime.utcnow()

        # Update database
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.update_agent_run_status(self.run_id, RunStatus.FAILED)
            await session.commit()

    async def get_state(self) -> Optional[WorkflowState]:
        """Get current workflow state."""
        return self.state

    async def cancel(self) -> None:
        """Cancel workflow execution."""
        if self.state is None:
            return

        self.state.status = WorkflowStatus.CANCELLED
        self.state.completed_at = datetime.utcnow()

        # Update database
        async for session in get_async_session():
            audit = AuditLogger(session)
            await audit.update_agent_run_status(self.run_id, RunStatus.CANCELLED)
            await session.commit()

