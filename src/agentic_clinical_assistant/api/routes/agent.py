"""Agent API routes."""

import asyncio
from datetime import datetime
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from agentic_clinical_assistant.api.models.agent import (
    AgentRunRequest,
    AgentRunResponse,
    AgentStatusResponse,
)
from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.database.models.agent_run import AgentRun, RunStatus
from agentic_clinical_assistant.workflow.executor import get_executor

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """
    Initiate an agent run.

    This endpoint accepts a user request and starts an agent workflow.
    The agent will process the request through multiple stages:
    1. Intake Agent - Classify request and assess risk
    2. Retrieval Agent - Find relevant evidence
    3. Synthesis Agent - Generate draft answer
    4. Verifier Agent - Verify safety and grounding

    Returns a run_id that can be used to check status.
    """
    async for session in get_async_session():
        audit = AuditLogger(session)

        try:
            # Log agent run start (this creates and returns the run_id)
            run_id = await audit.log_agent_run(
                request_text=request.request_text,
                user_id=request.user_id,
                extra_metadata=request.metadata,
            )

            # Commit the transaction
            await session.commit()

            # Start workflow execution in background
            executor = get_executor()
            asyncio.create_task(
                executor.execute_workflow(
                    run_id=run_id,
                    request_text=request.request_text,
                    user_id=request.user_id,
                )
            )

            return AgentRunResponse(
                run_id=run_id,
                status=RunStatus.PENDING.value,
                created_at=datetime.utcnow(),
                message="Agent run initiated successfully",
            )

        except Exception as e:
            # If run_id was created, mark as failed
            if "run_id" in locals():
                try:
                    await audit.update_agent_run_status(run_id, RunStatus.FAILED)
                    await session.commit()
                except Exception:
                    pass  # Ignore errors during cleanup
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate agent run: {str(e)}",
            )


@router.get("/status/{run_id}", response_model=AgentStatusResponse)
async def get_agent_status(run_id: UUID) -> AgentStatusResponse:
    """
    Get the status of an agent run.

    Returns detailed information about the agent run including:
    - Current status
    - Progress information
    - Final answer (if completed)
    - Error messages (if failed)
    """
    async for session in get_async_session():
        try:
            # Try to get state from workflow executor first
            executor = get_executor()
            workflow_state = await executor.get_workflow_state(run_id)
            
            if workflow_state:
                # Build progress from workflow state
                progress = None
                if workflow_state.get("status") in ["running", "intake", "retrieval", "synthesis", "verification"]:
                    progress = {
                        "current_step": workflow_state.get("current_step", "processing"),
                        "steps_completed": workflow_state.get("steps_completed", 0),
                        "total_steps": workflow_state.get("total_steps", 4),
                    }

                # Parse datetime strings safely
                def parse_datetime(dt_str):
                    if not dt_str:
                        return None
                    if isinstance(dt_str, datetime):
                        return dt_str
                    # Handle ISO format with or without timezone
                    dt_str = dt_str.replace('Z', '+00:00')
                    return datetime.fromisoformat(dt_str)
                
                return AgentStatusResponse(
                    run_id=UUID(workflow_state["run_id"]),
                    status=workflow_state["status"],
                    request_text=workflow_state["request_text"],
                    request_type=workflow_state.get("request_type"),
                    risk_label=workflow_state.get("risk_label"),
                    created_at=parse_datetime(workflow_state["created_at"]),
                    started_at=parse_datetime(workflow_state.get("started_at")),
                    completed_at=parse_datetime(workflow_state.get("completed_at")),
                    final_answer=workflow_state.get("final_answer"),
                    abstention_reason=workflow_state.get("abstention_reason"),
                    error_message=workflow_state.get("error_message"),
                    progress=progress,
                    metadata=workflow_state.get("metadata", {}),
                )

            # Fallback to database
            run = await session.get(AgentRun, run_id)
            if run is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent run {run_id} not found",
                )

            # Build progress information
            progress = None
            if run.status == RunStatus.RUNNING:
                progress = {
                    "current_step": "processing",
                    "steps_completed": 0,
                    "total_steps": 4,
                }

            return AgentStatusResponse(
                run_id=run.run_id,
                status=run.status.value,
                request_text=run.request_text,
                request_type=run.request_type,
                risk_label=run.risk_label,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                final_answer=run.final_answer,
                abstention_reason=run.abstention_reason,
                error_message=None,
                progress=progress,
                metadata=run.metadata,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get agent status: {str(e)}",
            )


@router.post("/cancel/{run_id}")
async def cancel_agent_run(run_id: UUID) -> Dict[str, str]:
    """
    Cancel a running agent workflow.

    Args:
        run_id: Agent run identifier

    Returns:
        Cancellation status
    """
    executor = get_executor()
    cancelled = await executor.cancel_workflow(run_id)
    
    if cancelled:
        return {"status": "cancelled", "run_id": str(run_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {run_id} not found or already completed",
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "agent-orchestrator"}

