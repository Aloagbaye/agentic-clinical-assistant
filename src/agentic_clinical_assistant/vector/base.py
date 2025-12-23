"""Abstract base class for vector database adapters."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class VectorDBBackend(str, Enum):
    """Supported vector database backends."""

    FAISS = "faiss"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class Document(BaseModel):
    """Document model for vector storage."""

    id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    doc_hash: Optional[str] = None  # SHA-256 hash for verification


class SearchResult(BaseModel):
    """Search result model."""

    document: Document
    score: float
    doc_hash: str


class VectorDB(ABC):
    """Abstract base class for vector database adapters."""

    def __init__(self, backend: VectorDBBackend):
        """Initialize vector database adapter."""
        self.backend = backend

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector database connection/index."""
        pass

    @abstractmethod
    async def add_documents(
        self, documents: List[Document], batch_size: Optional[int] = None
    ) -> List[str]:
        """
        Add documents to the vector database.

        Args:
            documents: List of documents to add
            batch_size: Optional batch size for bulk operations

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filters: Metadata filters to apply
            **kwargs: Additional backend-specific parameters

        Returns:
            List of search results with scores
        """
        pass

    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents by IDs.

        Args:
            document_ids: List of document IDs to delete
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def update_document(self, document: Document) -> None:
        """
        Update an existing document.

        Args:
            document: Document with updated fields
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        pass

