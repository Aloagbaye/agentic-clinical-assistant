"""Workflow executor for running workflows in background."""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from agentic_clinical_assistant.workflow.engine import WorkflowEngine


class WorkflowExecutor:
    """Executes workflows in background tasks."""

    def __init__(self):
        """Initialize workflow executor."""
        self.running_workflows: dict[uuid.UUID, asyncio.Task] = {}

    async def execute_workflow(
        self,
        run_id: uuid.UUID,
        request_text: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Execute a workflow in the background.

        Args:
            run_id: Agent run identifier
            request_text: User's request
            user_id: Optional user identifier
        """
        engine = WorkflowEngine(run_id)
        await engine.initialize(request_text, user_id)

        # Create background task
        task = asyncio.create_task(engine.execute())
        self.running_workflows[run_id] = task

        try:
            await task
        except Exception as e:
            # Error handling is done in the engine
            pass
        finally:
            # Remove from running workflows
            self.running_workflows.pop(run_id, None)

    async def get_workflow_state(self, run_id: uuid.UUID) -> Optional[dict]:
        """
        Get current state of a workflow.

        Args:
            run_id: Agent run identifier

        Returns:
            Workflow state dictionary or None if not found
        """
        # Check if workflow is running
        if run_id in self.running_workflows:
            # Create engine to get state
            engine = WorkflowEngine(run_id)
            state = await engine.get_state()
            if state:
                return state.to_dict()

            # Try to get from database
            from agentic_clinical_assistant.database import get_async_session
            from agentic_clinical_assistant.database.models.agent_run import AgentRun

            async for session in get_async_session():
                run = await session.get(AgentRun, run_id)
                if run:
                    return {
                        "run_id": str(run.run_id),
                        "status": run.status.value,
                        "request_text": run.request_text,
                        "user_id": run.user_id,
                        "request_type": run.request_type,
                        "risk_label": run.risk_label,
                        "created_at": run.created_at.isoformat(),
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "final_answer": run.final_answer,
                        "abstention_reason": run.abstention_reason,
                        "metadata": run.metadata or {},
                    }
                return None

    async def cancel_workflow(self, run_id: uuid.UUID) -> bool:
        """
        Cancel a running workflow.

        Args:
            run_id: Agent run identifier

        Returns:
            True if workflow was cancelled, False otherwise
        """
        if run_id in self.running_workflows:
            task = self.running_workflows[run_id]
            task.cancel()
            self.running_workflows.pop(run_id, None)

            # Update engine state
            engine = WorkflowEngine(run_id)
            await engine.cancel()
            return True

        return False


# Global executor instance
_executor: Optional[WorkflowExecutor] = None


def get_executor() -> WorkflowExecutor:
    """Get global workflow executor instance."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor()
    return _executor

