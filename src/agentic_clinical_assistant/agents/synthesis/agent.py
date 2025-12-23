"""Synthesis Agent - Generates draft answers with citations."""

from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.agents.synthesis.models import Citation, DraftAnswer, SynthesisResult
from agentic_clinical_assistant.config import settings


class SynthesisAgent:
    """Synthesis Agent for answer generation."""

    def __init__(self):
        """Initialize Synthesis Agent."""
        self.answer_template = """Based on the provided evidence, here is the answer:

{answer}

Citations:
{citations}
"""

    async def generate_answer(
        self,
        request_text: str,
        evidence: List[Dict[str, Any]],
    ) -> SynthesisResult:
        """
        Generate draft answer from evidence.

        Args:
            request_text: Original user request
            evidence: Retrieved evidence items

        Returns:
            SynthesisResult with draft answer and citations
        """
        if not evidence:
            return SynthesisResult(
                draft_answer="I could not find relevant information to answer your question.",
                citations=[],
                confidence=0.0,
                metadata={"reason": "no_evidence"},
            )

        # Extract text from evidence
        evidence_texts = [item.get("text", "") for item in evidence]
        
        # Generate answer (placeholder - will use LLM in full implementation)
        answer = self._generate_answer_text(request_text, evidence_texts)
        
        # Create citations
        citations = self._create_citations(evidence)
        
        # Calculate confidence
        confidence = self._calculate_confidence(evidence)

        draft = DraftAnswer(
            answer=answer,
            citations=citations,
            confidence=confidence,
            metadata={
                "evidence_count": len(evidence),
                "request": request_text,
            },
        )

        return SynthesisResult.from_draft_answer(draft)

    def _generate_answer_text(self, request: str, evidence_texts: List[str]) -> str:
        """Generate answer text from evidence."""
        # Placeholder implementation
        # In full implementation, this would use an LLM with constrained prompting
        
        if not evidence_texts:
            return "I could not find relevant information to answer your question."
        
        # Simple template-based answer for now
        combined_evidence = "\n\n".join(evidence_texts[:3])  # Use top 3 evidence items
        
        answer = f"""Based on the available documentation:

{combined_evidence[:500]}...

This information addresses your question: "{request}"
"""
        return answer

    def _create_citations(self, evidence: List[Dict[str, Any]]) -> List[Citation]:
        """Create citations from evidence."""
        citations = []
        
        for item in evidence:
            citation = Citation(
                claim=item.get("text", "")[:100],  # First 100 chars as claim
                document_id=item.get("document_id", ""),
                doc_hash=item.get("doc_hash", ""),
                score=item.get("score", 0.0),
                text_snippet=item.get("text", "")[:200],  # First 200 chars as snippet
                metadata=item.get("metadata", {}),
            )
            citations.append(citation)
        
        return citations

    def _calculate_confidence(self, evidence: List[Dict[str, Any]]) -> float:
        """Calculate answer confidence based on evidence."""
        if not evidence:
            return 0.0
        
        # Average score of top evidence
        scores = [item.get("score", 0.0) for item in evidence]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # More evidence = higher confidence
        evidence_factor = min(len(evidence) / 5.0, 1.0)  # Cap at 5 evidence items
        
        confidence = (avg_score * 0.7) + (evidence_factor * 0.3)
        return min(confidence, 1.0)

