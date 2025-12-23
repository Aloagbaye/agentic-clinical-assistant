"""FAISS vector database adapter."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.vector.base import Document, SearchResult, VectorDB, VectorDBBackend


class FAISSAdapter(VectorDB):
    """FAISS vector database adapter for local similarity search."""

    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: Optional[int] = None,
    ):
        """
        Initialize FAISS adapter.

        Args:
            index_path: Path to save/load FAISS index
            dimension: Embedding dimension
        """
        super().__init__(VectorDBBackend.FAISS)
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self.dimension = dimension or settings.FAISS_DIMENSION
        self.index: Optional[faiss.Index] = None
        self.documents: Dict[str, Document] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}

    async def initialize(self) -> None:
        """Initialize or load FAISS index."""
        # Create directory if it doesn't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing index if it exists
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.json"

        if index_file.exists() and metadata_file.exists():
            # Load existing index
            self.index = faiss.read_index(str(index_file))
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                self.documents = {
                    doc_id: Document(**doc_data) for doc_id, doc_data in metadata["documents"].items()
                }
                self.id_to_index = metadata["id_to_index"]
                self.index_to_id = {v: k for k, v in self.id_to_index.items()}
        else:
            # Create new index (L2 distance)
            self.index = faiss.IndexFlatL2(self.dimension)

    async def add_documents(
        self, documents: List[Document], batch_size: Optional[int] = None
    ) -> List[str]:
        """Add documents to FAISS index."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        document_ids = []
        embeddings = []

        for doc in documents:
            if doc.embedding is None:
                raise ValueError(f"Document {doc.id} missing embedding")

            if len(doc.embedding) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.dimension}, got {len(doc.embedding)}"
                )

            # Add to index
            idx = self.index.ntotal
            self.index.add(np.array([doc.embedding], dtype=np.float32))

            # Store document metadata
            self.documents[doc.id] = doc
            self.id_to_index[doc.id] = idx
            self.index_to_id[idx] = doc.id
            document_ids.append(doc.id)

        await self._save_index()
        return document_ids

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        if len(query_embedding) != self.dimension:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.dimension}, got {len(query_embedding)}"
            )

        # Search in FAISS
        query_vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty results
                continue

            doc_id = self.index_to_id.get(idx)
            if doc_id is None:
                continue

            doc = self.documents.get(doc_id)
            if doc is None:
                continue

            # Apply metadata filters if provided
            if filters:
                if not self._matches_filters(doc.metadata, filters):
                    continue

            # Convert L2 distance to similarity score (lower distance = higher similarity)
            # Normalize to 0-1 range (assuming max distance of 10)
            score = max(0.0, 1.0 - (float(distance) / 10.0))

            results.append(
                SearchResult(
                    document=doc,
                    score=score,
                    doc_hash=doc.doc_hash or "",
                )
            )

        return results[:top_k]

    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
        return True

    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents (FAISS doesn't support deletion, so we mark as deleted)."""
        for doc_id in document_ids:
            if doc_id in self.documents:
                # FAISS doesn't support deletion, so we remove from metadata
                # The index entry remains but won't be returned in searches
                del self.documents[doc_id]
                if doc_id in self.id_to_index:
                    idx = self.id_to_index[doc_id]
                    del self.id_to_index[doc_id]
                    del self.index_to_id[idx]

        await self._save_index()

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(document_id)

    async def update_document(self, document: Document) -> None:
        """Update document (FAISS doesn't support updates, so we delete and re-add)."""
        if document.id in self.documents:
            await self.delete_documents([document.id])
        await self.add_documents([document])

    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if self.index is None:
            return {"total_documents": 0, "dimension": self.dimension}

        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal,
            "dimension": self.dimension,
            "backend": self.backend.value,
        }

    async def close(self) -> None:
        """Save index and close."""
        await self._save_index()

    async def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            return

        # Save FAISS index
        index_file = self.index_path / "index.faiss"
        faiss.write_index(self.index, str(index_file))

        # Save metadata
        metadata_file = self.index_path / "metadata.json"
        metadata = {
            "documents": {doc_id: doc.model_dump() for doc_id, doc in self.documents.items()},
            "id_to_index": self.id_to_index,
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

