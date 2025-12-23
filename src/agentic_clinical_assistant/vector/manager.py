"""Vector database manager with unified interface and backend selection."""

from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.vector.base import Document, SearchResult, VectorDB, VectorDBBackend
from agentic_clinical_assistant.vector.faiss_adapter import FAISSAdapter
from agentic_clinical_assistant.vector.pinecone_adapter import PineconeAdapter
from agentic_clinical_assistant.vector.weaviate_adapter import WeaviateAdapter


class VectorDBManager:
    """Manager for multiple vector database backends with unified interface."""

    def __init__(self):
        """Initialize vector database manager."""
        self.adapters: Dict[VectorDBBackend, VectorDB] = {}
        self.default_backend = VectorDBBackend(settings.DEFAULT_VECTOR_BACKEND)
        self.enable_multi_backend = settings.ENABLE_MULTI_BACKEND_RETRIEVAL

    async def initialize(self, backends: Optional[List[VectorDBBackend]] = None) -> None:
        """
        Initialize vector database adapters.

        Args:
            backends: List of backends to initialize (default: all)
        """
        if backends is None:
            backends = [VectorDBBackend.FAISS, VectorDBBackend.PINECONE, VectorDBBackend.WEAVIATE]

        for backend in backends:
            if backend == VectorDBBackend.FAISS:
                adapter = FAISSAdapter()
            elif backend == VectorDBBackend.PINECONE:
                if settings.PINECONE_API_KEY:
                    adapter = PineconeAdapter()
                else:
                    continue  # Skip if no API key
            elif backend == VectorDBBackend.WEAVIATE:
                adapter = WeaviateAdapter()
            else:
                continue

            try:
                await adapter.initialize()
                self.adapters[backend] = adapter
            except Exception as e:
                # Log error but continue with other backends
                print(f"Warning: Failed to initialize {backend.value}: {e}")

    def get_adapter(self, backend: Optional[VectorDBBackend] = None) -> VectorDB:
        """
        Get adapter for specified backend.

        Args:
            backend: Backend to use (default: configured default)

        Returns:
            VectorDB adapter instance
        """
        backend = backend or self.default_backend
        if backend not in self.adapters:
            raise ValueError(f"Backend {backend.value} not initialized")
        return self.adapters[backend]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def add_documents(
        self,
        documents: List[Document],
        backend: Optional[VectorDBBackend] = None,
        batch_size: Optional[int] = None,
    ) -> List[str]:
        """
        Add documents to vector database.

        Args:
            documents: Documents to add
            backend: Backend to use (default: configured default)
            batch_size: Batch size for bulk operations

        Returns:
            List of document IDs
        """
        adapter = self.get_adapter(backend)
        return await adapter.add_documents(documents, batch_size=batch_size)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        backend: Optional[VectorDBBackend] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filters: Metadata filters
            backend: Backend to use (None = use default or multi-backend)
            **kwargs: Additional backend-specific parameters

        Returns:
            List of search results
        """
        if backend is not None:
            # Single backend search
            adapter = self.get_adapter(backend)
            return await adapter.search(query_embedding, top_k=top_k, filters=filters, **kwargs)

        if self.enable_multi_backend and len(self.adapters) > 1:
            # Multi-backend search - query all and merge results
            return await self._multi_backend_search(
                query_embedding, top_k=top_k, filters=filters, **kwargs
            )

        # Default backend search
        adapter = self.get_adapter()
        return await adapter.search(query_embedding, top_k=top_k, filters=filters, **kwargs)

    async def _multi_backend_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search across multiple backends and merge results."""
        import asyncio

        # Query all backends in parallel
        tasks = [
            adapter.search(query_embedding, top_k=top_k, filters=filters, **kwargs)
            for adapter in self.adapters.values()
        ]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        all_results: Dict[str, SearchResult] = {}
        for results in results_list:
            if isinstance(results, Exception):
                continue
            for result in results:
                doc_hash = result.doc_hash
                if doc_hash not in all_results:
                    all_results[doc_hash] = result
                else:
                    # Average scores if same document found in multiple backends
                    existing = all_results[doc_hash]
                    all_results[doc_hash] = SearchResult(
                        document=result.document,
                        score=(existing.score + result.score) / 2.0,
                        doc_hash=doc_hash,
                    )

        # Sort by score and return top_k
        sorted_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:top_k]

    async def delete_documents(
        self, document_ids: List[str], backend: Optional[VectorDBBackend] = None
    ) -> None:
        """Delete documents from vector database."""
        adapter = self.get_adapter(backend)
        await adapter.delete_documents(document_ids)

    async def get_document(
        self, document_id: str, backend: Optional[VectorDBBackend] = None
    ) -> Optional[Document]:
        """Get document by ID."""
        adapter = self.get_adapter(backend)
        return await adapter.get_document(document_id)

    async def update_document(
        self, document: Document, backend: Optional[VectorDBBackend] = None
    ) -> None:
        """Update document in vector database."""
        adapter = self.get_adapter(backend)
        await adapter.update_document(document)

    async def get_stats(
        self, backend: Optional[VectorDBBackend] = None
    ) -> Dict[str, Any]:
        """Get database statistics."""
        if backend:
            adapter = self.get_adapter(backend)
            return await adapter.get_stats()

        # Return stats for all backends
        all_stats = {}
        for backend_name, adapter in self.adapters.items():
            all_stats[backend_name.value] = await adapter.get_stats()
        return all_stats

    async def close(self) -> None:
        """Close all adapter connections."""
        for adapter in self.adapters.values():
            await adapter.close()
        self.adapters.clear()

