"""Tests for workflow engine."""

import pytest
import uuid
from datetime import datetime

from agentic_clinical_assistant.workflow.engine import WorkflowEngine
from agentic_clinical_assistant.workflow.state import (
    StepStatus,
    WorkflowStatus,
    WorkflowState,
)


@pytest.mark.asyncio
async def test_workflow_initialization():
    """Test workflow initialization."""
    run_id = uuid.uuid4()
    engine = WorkflowEngine(run_id)
    
    state = await engine.initialize(
        request_text="Test request",
        user_id="test_user"
    )
    
    assert state.run_id == run_id
    assert state.status == WorkflowStatus.PENDING
    assert state.request_text == "Test request"
    assert state.user_id == "test_user"


@pytest.mark.asyncio
async def test_workflow_state_to_dict():
    """Test workflow state serialization."""
    run_id = uuid.uuid4()
    state = WorkflowState(
        run_id=run_id,
        status=WorkflowStatus.RUNNING,
        request_text="Test request",
    )
    
    state_dict = state.to_dict()
    
    assert state_dict["run_id"] == str(run_id)
    assert state_dict["status"] == "running"
    assert state_dict["request_text"] == "Test request"


def test_step_result():
    """Test step result creation."""
    from agentic_clinical_assistant.workflow.state import StepResult
    
    result = StepResult(
        step_name="test_step",
        status=StepStatus.COMPLETED,
        result={"key": "value"},
    )
    
    assert result.step_name == "test_step"
    assert result.status == StepStatus.COMPLETED
    assert result.result == {"key": "value"}

