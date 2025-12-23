"""Verifier Agent models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VerificationIssue(BaseModel):
    """Issue found during verification."""

    issue_type: str = Field(..., description="Type of issue")
    severity: str = Field(..., description="Severity level (low/medium/high)")
    description: str = Field(..., description="Issue description")
    location: Optional[str] = Field(None, description="Location in text where issue was found")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing")


class VerificationResult(BaseModel):
    """Verification result."""

    passed: bool = Field(..., description="Whether verification passed")
    status: str = Field(..., description="Verification status")
    issues: List[VerificationIssue] = Field(default_factory=list, description="Issues found")
    phi_detected: bool = Field(default=False, description="Whether PHI was detected")
    phi_count: int = Field(default=0, description="Number of PHI detections")
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Grounding score")
    reason: Optional[str] = Field(None, description="Reason for pass/fail")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

