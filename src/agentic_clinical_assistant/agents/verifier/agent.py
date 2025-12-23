"""Verifier Agent - Verifies safety and grounding."""

import re
from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.agents.verifier.models import VerificationIssue, VerificationResult


class VerifierAgent:
    """Verifier Agent for safety and grounding verification."""

    def __init__(self):
        """Initialize Verifier Agent."""
        # PHI/PII patterns
        self.phi_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{3}\.\d{2}\.\d{4}\b",  # SSN with dots
            r"\b\d{10}\b",  # 10-digit number (potential SSN)
            r"\b[A-Z]{2}\d{6}\b",  # Medical record number pattern
            r"\b\d{4}-\d{2}-\d{2}\b",  # Date (could be DOB)
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # Date format
        ]
        
        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+(?:previous|above|all)\s+instructions?",
            r"forget\s+(?:previous|above|all)",
            r"system\s*:\s*",
            r"assistant\s*:\s*",
            r"user\s*:\s*",
        ]

    async def verify(
        self,
        draft_answer: str,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationResult:
        """
        Verify draft answer for safety and grounding.

        Args:
            draft_answer: Draft answer to verify
            citations: Citations for the answer

        Returns:
            VerificationResult with verification status
        """
        issues: List[VerificationIssue] = []
        
        # Check for PHI/PII
        phi_result = self._check_phi(draft_answer)
        if phi_result["detected"]:
            issues.append(
                VerificationIssue(
                    issue_type="phi_detection",
                    severity="high",
                    description=f"Potential PHI/PII detected: {phi_result['count']} matches",
                    suggestion="Review and redact sensitive information",
                )
            )
        
        # Check for prompt injection
        injection_result = self._check_prompt_injection(draft_answer)
        if injection_result["detected"]:
            issues.append(
                VerificationIssue(
                    issue_type="prompt_injection",
                    severity="high",
                    description="Potential prompt injection detected",
                    suggestion="Review answer for embedded instructions",
                )
            )
        
        # Check grounding
        grounding_result = self._check_grounding(draft_answer, citations or [])
        
        # Determine if verification passes
        passed = (
            not phi_result["detected"]
            and not injection_result["detected"]
            and grounding_result["score"] >= 0.7
        )
        
        status = "pass" if passed else "fail"
        reason = None
        if not passed:
            if phi_result["detected"]:
                reason = "PHI/PII detected in answer"
            elif injection_result["detected"]:
                reason = "Prompt injection detected"
            elif grounding_result["score"] < 0.7:
                reason = "Insufficient grounding (low citation coverage)"

        return VerificationResult(
            passed=passed,
            status=status,
            issues=issues,
            phi_detected=phi_result["detected"],
            phi_count=phi_result["count"],
            grounding_score=grounding_result["score"],
            reason=reason,
            metadata={
                "phi_matches": phi_result.get("matches", []),
                "injection_matches": injection_result.get("matches", []),
                "grounding_details": grounding_result,
            },
        )

    def _check_phi(self, text: str) -> Dict[str, Any]:
        """Check for PHI/PII in text."""
        matches = []
        for pattern in self.phi_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        
        return {
            "detected": len(matches) > 0,
            "count": len(matches),
            "matches": matches[:10],  # Limit to first 10 matches
        }

    def _check_prompt_injection(self, text: str) -> Dict[str, Any]:
        """Check for prompt injection attempts."""
        matches = []
        for pattern in self.injection_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        
        return {
            "detected": len(matches) > 0,
            "count": len(matches),
            "matches": matches,
        }

    def _check_grounding(self, answer: str, citations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check grounding of answer in citations."""
        if not citations:
            return {
                "score": 0.0,
                "reason": "No citations provided",
            }
        
        # Simple heuristic: check if answer mentions citation-related terms
        citation_terms = ["according to", "based on", "per", "as stated", "document", "source"]
        answer_lower = answer.lower()
        
        citation_mentions = sum(1 for term in citation_terms if term in answer_lower)
        citation_coverage = min(citation_mentions / len(citations), 1.0) if citations else 0.0
        
        # Score based on citation coverage and number of citations
        score = (citation_coverage * 0.6) + (min(len(citations) / 5.0, 1.0) * 0.4)
        
        return {
            "score": score,
            "citation_count": len(citations),
            "citation_mentions": citation_mentions,
            "coverage": citation_coverage,
        }

