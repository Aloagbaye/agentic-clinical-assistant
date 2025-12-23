"""Intake Agent models."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequestType(str, Enum):
    """Types of requests."""

    POLICY_LOOKUP = "policy_lookup"
    SUMMARIZE_GUIDELINE = "summarize_guideline"
    COMPARE_PROTOCOLS = "compare_protocols"
    EXPLAIN_POLICY = "explain_policy"
    UNKNOWN = "unknown"


class RiskLabel(str, Enum):
    """Risk classification levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestPlan(BaseModel):
    """Request plan from Intake Agent."""

    request_type: RequestType = Field(..., description="Type of request")
    risk_label: RiskLabel = Field(..., description="Risk classification")
    required_tools: List[str] = Field(default_factory=list, description="Required tools for execution")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Extracted constraints")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Classification confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_type": self.request_type.value,
            "risk_label": self.risk_label.value,
            "required_tools": self.required_tools,
            "filters": self.constraints,  # Alias for compatibility
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

