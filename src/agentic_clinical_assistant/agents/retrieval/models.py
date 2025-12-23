"""Retrieval Agent models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """Single evidence item from retrieval."""

    document_id: str = Field(..., description="Document identifier")
    text: str = Field(..., description="Document text")
    score: float = Field(..., description="Relevance score")
    doc_hash: str = Field(..., description="Document hash")
    backend: str = Field(..., description="Vector backend used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class EvidenceBundle(BaseModel):
    """Bundle of evidence from retrieval."""

    query: str = Field(..., description="Original query")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Retrieved evidence")
    backends_queried: List[str] = Field(default_factory=list, description="Backends queried")
    selected_backend: Optional[str] = Field(None, description="Selected backend")
    total_results: int = Field(default=0, description="Total results retrieved")
    retrieval_mode: str = Field(default="default", description="Retrieval mode used")


class RetrievalResult(BaseModel):
    """Complete retrieval result."""

    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence items")
    doc_hashes: List[str] = Field(default_factory=list, description="Document hashes")
    scores: List[float] = Field(default_factory=list, description="Relevance scores")
    backend: Optional[str] = Field(None, description="Backend used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_evidence_bundle(cls, bundle: EvidenceBundle) -> "RetrievalResult":
        """Create RetrievalResult from EvidenceBundle."""
        return cls(
            evidence=[
                {
                    "document_id": item.document_id,
                    "text": item.text,
                    "score": item.score,
                    "doc_hash": item.doc_hash,
                    "backend": item.backend,
                    "metadata": item.metadata,
                }
                for item in bundle.evidence
            ],
            doc_hashes=[item.doc_hash for item in bundle.evidence],
            scores=[item.score for item in bundle.evidence],
            backend=bundle.selected_backend,
            metadata={
                "backends_queried": bundle.backends_queried,
                "retrieval_mode": bundle.retrieval_mode,
                "total_results": bundle.total_results,
            },
        )

