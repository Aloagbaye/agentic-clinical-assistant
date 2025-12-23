"""Workflow state management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    INTAKE = "intake"
    RETRIEVAL = "retrieval"
    SYNTHESIS = "synthesis"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"
    ABSTAINED = "abstained"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Individual step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a workflow step."""

    step_name: str
    status: StepStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
    """State of a workflow execution."""

    run_id: UUID
    status: WorkflowStatus
    request_text: str
    user_id: Optional[str] = None
    
    # Step results
    intake_result: Optional[StepResult] = None
    retrieval_result: Optional[StepResult] = None
    synthesis_result: Optional[StepResult] = None
    verification_result: Optional[StepResult] = None
    
    # Workflow metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Final outputs
    final_answer: Optional[str] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)
    abstention_reason: Optional[str] = None
    error_message: Optional[str] = None
    
    # Progress tracking
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 4
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "run_id": str(self.run_id),
            "status": self.status.value,
            "request_text": self.request_text,
            "user_id": self.user_id,
            "intake_result": self.intake_result.__dict__ if self.intake_result else None,
            "retrieval_result": self.retrieval_result.__dict__ if self.retrieval_result else None,
            "synthesis_result": self.synthesis_result.__dict__ if self.synthesis_result else None,
            "verification_result": self.verification_result.__dict__ if self.verification_result else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "final_answer": self.final_answer,
            "citations": self.citations,
            "abstention_reason": self.abstention_reason,
            "error_message": self.error_message,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "metadata": self.metadata,
        }

