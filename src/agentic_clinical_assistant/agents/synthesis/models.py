"""Synthesis Agent models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation for a claim."""

    claim: str = Field(..., description="The claim being cited")
    document_id: str = Field(..., description="Source document ID")
    doc_hash: str = Field(..., description="Document hash")
    score: float = Field(..., description="Relevance score")
    text_snippet: str = Field(..., description="Relevant text snippet")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Citation metadata")


class DraftAnswer(BaseModel):
    """Draft answer with citations."""

    answer: str = Field(..., description="Generated answer text")
    citations: List[Citation] = Field(default_factory=list, description="Citations for claims")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Answer confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SynthesisResult(BaseModel):
    """Complete synthesis result."""

    draft_answer: str = Field(..., description="Draft answer text")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citations")
    confidence: float = Field(default=0.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_draft_answer(cls, draft: DraftAnswer) -> "SynthesisResult":
        """Create SynthesisResult from DraftAnswer."""
        return cls(
            draft_answer=draft.answer,
            citations=[
                {
                    "claim": cit.claim,
                    "document_id": cit.document_id,
                    "doc_hash": cit.doc_hash,
                    "score": cit.score,
                    "text_snippet": cit.text_snippet,
                    "metadata": cit.metadata,
                }
                for cit in draft.citations
            ],
            confidence=draft.confidence,
            metadata=draft.metadata,
        )

