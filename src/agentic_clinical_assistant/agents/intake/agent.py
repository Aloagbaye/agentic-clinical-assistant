"""Intake Agent - Classifies requests and assesses risk."""

import re
from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.agents.intake.models import RequestPlan, RequestType, RiskLabel


class IntakeAgent:
    """Intake Agent for request classification and risk assessment."""

    def __init__(self):
        """Initialize Intake Agent."""
        self.request_type_keywords = {
            RequestType.POLICY_LOOKUP: [
                "policy", "protocol", "procedure", "guideline", "standard",
                "what is", "how to", "what are", "show me",
            ],
            RequestType.SUMMARIZE_GUIDELINE: [
                "summarize", "summary", "overview", "brief", "outline",
            ],
            RequestType.COMPARE_PROTOCOLS: [
                "compare", "difference", "versus", "vs", "contrast",
                "which is better", "what's the difference",
            ],
            RequestType.EXPLAIN_POLICY: [
                "explain", "describe", "walk through", "step by step",
                "how does", "why", "what does",
            ],
        }

        self.risk_keywords = {
            RiskLabel.HIGH: [
                "diagnosis", "treat", "treatment", "prescribe", "medication",
                "patient", "diagnose", "cure", "therapy",
            ],
            RiskLabel.MEDIUM: [
                "recommend", "suggest", "advise", "guidance", "best practice",
            ],
            RiskLabel.LOW: [
                "policy", "procedure", "protocol", "guideline", "standard",
                "documentation", "process",
            ],
        }

    async def classify_request(self, request_text: str) -> RequestPlan:
        """
        Classify request and assess risk.

        Args:
            request_text: User's request

        Returns:
            RequestPlan with classification and risk assessment
        """
        request_text_lower = request_text.lower()

        # Classify request type
        request_type = self._classify_request_type(request_text_lower)
        
        # Assess risk
        risk_label = self._assess_risk(request_text_lower, request_type)
        
        # Extract constraints
        constraints = self._extract_constraints(request_text)
        
        # Determine required tools
        required_tools = self._determine_required_tools(request_type, risk_label)
        
        # Calculate confidence
        confidence = self._calculate_confidence(request_text_lower, request_type, risk_label)

        return RequestPlan(
            request_type=request_type,
            risk_label=risk_label,
            required_tools=required_tools,
            constraints=constraints,
            confidence=confidence,
            metadata={
                "original_request": request_text,
            },
        )

    def _classify_request_type(self, request_lower: str) -> RequestType:
        """Classify the type of request."""
        scores = {}
        
        for req_type, keywords in self.request_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in request_lower)
            if score > 0:
                scores[req_type] = score
        
        if scores:
            return max(scores, key=scores.get)  # type: ignore
        
        return RequestType.UNKNOWN

    def _assess_risk(self, request_lower: str, request_type: RequestType) -> RiskLabel:
        """Assess risk level of the request."""
        # Check for high-risk keywords
        high_risk_score = sum(1 for keyword in self.risk_keywords[RiskLabel.HIGH] if keyword in request_lower)
        if high_risk_score > 0:
            return RiskLabel.HIGH
        
        # Check for medium-risk keywords
        medium_risk_score = sum(1 for keyword in self.risk_keywords[RiskLabel.MEDIUM] if keyword in request_lower)
        if medium_risk_score > 0:
            return RiskLabel.MEDIUM
        
        # Default to low risk for policy/procedure queries
        return RiskLabel.LOW

    def _extract_constraints(self, request_text: str) -> Dict[str, Any]:
        """Extract constraints from request."""
        constraints = {}
        
        # Extract department
        department_patterns = [
            r"(?:in|for|from)\s+(?:the\s+)?(?:ER|ED|ICU|OR|department|dept)",
            r"(?:ER|ED|ICU|OR)\s+(?:department|dept)?",
        ]
        for pattern in department_patterns:
            match = re.search(pattern, request_text, re.IGNORECASE)
            if match:
                constraints["department"] = match.group(0)
                break
        
        # Extract jurisdiction/location
        location_patterns = [
            r"(?:in|for|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, request_text)
            if match:
                constraints["location"] = match.group(1)
                break
        
        # Extract timeframe
        timeframe_patterns = [
            r"(?:in|within|by)\s+(\d+)\s+(?:days?|weeks?|months?|years?)",
            r"(?:since|after|before)\s+(\d{4}-\d{2}-\d{2})",
        ]
        for pattern in timeframe_patterns:
            match = re.search(pattern, request_text, re.IGNORECASE)
            if match:
                constraints["timeframe"] = match.group(0)
                break
        
        return constraints

    def _determine_required_tools(self, request_type: RequestType, risk_label: RiskLabel) -> List[str]:
        """Determine required tools based on request type and risk."""
        tools = ["retrieve_evidence"]
        
        if risk_label == RiskLabel.HIGH:
            tools.append("redact_phi")
            tools.append("verify_grounding")
        
        if request_type == RequestType.COMPARE_PROTOCOLS:
            tools.append("compare_documents")
        
        return tools

    def _calculate_confidence(self, request_lower: str, request_type: RequestType, risk_label: RiskLabel) -> float:
        """Calculate classification confidence."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if request type is clearly identified
        if request_type != RequestType.UNKNOWN:
            confidence += 0.2
        
        # Increase confidence if risk keywords are found
        risk_keywords_found = sum(
            1 for keywords in self.risk_keywords.values()
            for keyword in keywords
            if keyword in request_lower
        )
        if risk_keywords_found > 0:
            confidence += 0.2
        
        # Increase confidence if constraints are extracted
        # (This would be done in a real implementation)
        confidence += 0.1
        
        return min(confidence, 1.0)

