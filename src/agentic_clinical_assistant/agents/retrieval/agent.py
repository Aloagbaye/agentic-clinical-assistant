"""Retrieval Agent - Retrieves evidence from vector databases."""

from typing import Any, Dict, List, Optional

from agentic_clinical_assistant.agents.retrieval.models import EvidenceBundle, EvidenceItem, RetrievalResult
from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.vector import VectorDBManager
from agentic_clinical_assistant.vector.base import VectorDBBackend
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator


class RetrievalAgent:
    """Retrieval Agent for evidence retrieval."""

    def __init__(self):
        """Initialize Retrieval Agent."""
        self.vector_manager: Optional[VectorDBManager] = None
        self.embedding_generator = get_embedding_generator()
        self.default_top_k = 10

    async def initialize(self) -> None:
        """Initialize vector database manager."""
        if self.vector_manager is None:
            self.vector_manager = VectorDBManager()
            # TODO: Initialize with configured backends
            # await self.vector_manager.initialize(backends=[...])

    async def retrieve_evidence(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        backends: Optional[List[str]] = None,
    ) -> RetrievalResult:
        """
        Retrieve evidence for a query.

        Args:
            query: Search query
            top_k: Number of results to retrieve
            filters: Metadata filters
            backends: Specific backends to query (None = all configured)

        Returns:
            RetrievalResult with evidence
        """
        await self.initialize()

        if self.vector_manager is None:
            raise RuntimeError("Vector manager not initialized")

        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Determine which backends to query
        if backends is None:
            backends = ["faiss"]  # Default to FAISS for now
            # TODO: Get from settings or use all configured backends

        # Query backends
        evidence_bundle = await self._query_backends(
            query=query,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters or {},
            backends=backends,
        )

        # Convert to RetrievalResult
        return RetrievalResult.from_evidence_bundle(evidence_bundle)

    async def _query_backends(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int,
        filters: Dict[str, Any],
        backends: List[str],
    ) -> EvidenceBundle:
        """Query multiple backends and aggregate results."""
        all_evidence: List[EvidenceItem] = []
        backends_queried = []

        for backend_name in backends:
            try:
                # Get backend
                backend_enum = VectorDBBackend(backend_name.lower())
                
                # Query backend
                # TODO: Actually query the backend using vector_manager
                # For now, return empty results
                # results = await self.vector_manager.search(
                #     query_embedding=query_embedding,
                #     top_k=top_k,
                #     filters=filters,
                #     backend=backend_enum,
                # )
                
                # Placeholder: Create empty results
                results = []
                
                # Convert to EvidenceItem
                for result in results:
                    evidence_item = EvidenceItem(
                        document_id=result.document.id,
                        text=result.document.text,
                        score=result.score,
                        doc_hash=result.document.doc_hash or "",
                        backend=backend_name,
                        metadata=result.document.metadata,
                    )
                    all_evidence.append(evidence_item)
                
                backends_queried.append(backend_name)
                
            except Exception as e:
                # Log error but continue with other backends
                print(f"Error querying backend {backend_name}: {e}")
                continue

        # Select best backend (for now, just use first)
        selected_backend = backends_queried[0] if backends_queried else None

        # Sort by score
        all_evidence.sort(key=lambda x: x.score, reverse=True)

        # Take top_k
        top_evidence = all_evidence[:top_k]

        return EvidenceBundle(
            query=query,
            evidence=top_evidence,
            backends_queried=backends_queried,
            selected_backend=selected_backend,
            total_results=len(top_evidence),
            retrieval_mode="multi_backend" if len(backends) > 1 else "single_backend",
        )

