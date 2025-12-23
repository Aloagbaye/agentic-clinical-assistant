"""Pinecone vector database adapter."""

from typing import Any, Dict, List, Optional

from pinecone import Pinecone, ServerlessSpec

from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.vector.base import Document, SearchResult, VectorDB, VectorDBBackend


class PineconeAdapter(VectorDB):
    """Pinecone vector database adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        """
        Initialize Pinecone adapter.

        Args:
            api_key: Pinecone API key
            environment: Pinecone environment/region
            index_name: Name of the Pinecone index
        """
        super().__init__(VectorDBBackend.PINECONE)
        self.api_key = api_key or settings.PINECONE_API_KEY
        self.environment = environment or settings.PINECONE_ENVIRONMENT
        self.index_name = index_name or settings.PINECONE_INDEX_NAME
        self.pc: Optional[Pinecone] = None
        self.index = None

    async def initialize(self) -> None:
        """Initialize Pinecone connection and index."""
        if not self.api_key:
            raise ValueError("Pinecone API key is required")

        self.pc = Pinecone(api_key=self.api_key)

        # Check if index exists, create if not
        indexes_response = self.pc.list_indexes()
        # Handle both dict and object responses
        if hasattr(indexes_response, 'names'):
            index_names = indexes_response.names()
        elif isinstance(indexes_response, dict):
            index_names = indexes_response.get('names', [])
        else:
            # Fallback: try to get names from the response
            index_names = [idx.name if hasattr(idx, 'name') else idx for idx in indexes_response] if hasattr(indexes_response, '__iter__') else []
        
        if self.index_name not in index_names:
            # Get dimension from settings (or create with default)
            from agentic_clinical_assistant.vector.embeddings import get_embedding_generator

            generator = get_embedding_generator()
            dimension = generator.dimension

            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=self.environment),
            )

        self.index = self.pc.Index(self.index_name)

    async def add_documents(
        self, documents: List[Document], batch_size: Optional[int] = None
    ) -> List[str]:
        """Add documents to Pinecone index."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        batch_size = batch_size or 100
        document_ids = []

        # Prepare vectors for Pinecone
        vectors = []
        for doc in documents:
            if doc.embedding is None:
                raise ValueError(f"Document {doc.id} missing embedding")

            # Pinecone format: (id, vector, metadata)
            vectors.append(
                {
                    "id": doc.id,
                    "values": doc.embedding,
                    "metadata": {
                        **doc.metadata,
                        "text": doc.text,
                        "doc_hash": doc.doc_hash or "",
                    },
                }
            )
            document_ids.append(doc.id)

        # Upsert in batches
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch)

        return document_ids

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search for similar documents in Pinecone."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        # Build filter expression for Pinecone
        filter_dict = None
        if filters:
            filter_dict = {}
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_dict[key] = {"$in": value}
                else:
                    filter_dict[key] = value

        # Query Pinecone
        query_response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )

        results = []
        # Handle both dict and object responses
        matches = query_response.matches if hasattr(query_response, 'matches') else query_response.get('matches', [])
        for match in matches:
            # Handle both dict and object match types
            if isinstance(match, dict):
                match_id = match.get('id', '')
                match_score = match.get('score', 0.0)
                match_metadata = match.get('metadata', {})
            else:
                match_id = match.id if hasattr(match, 'id') else ''
                match_score = match.score if hasattr(match, 'score') else 0.0
                match_metadata = match.metadata if hasattr(match, 'metadata') else {}
            
            metadata = match_metadata or {}
            doc = Document(
                id=match_id,
                text=metadata.get("text", ""),
                metadata={k: v for k, v in metadata.items() if k not in ("text", "doc_hash")},
                doc_hash=metadata.get("doc_hash"),
            )

            results.append(
                SearchResult(
                    document=doc,
                    score=float(match_score),
                    doc_hash=doc.doc_hash or "",
                )
            )

        return results

    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Pinecone."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        # Pinecone delete by IDs
        self.index.delete(ids=document_ids)

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID from Pinecone."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            raise RuntimeError("Index not initialized")

        # Fetch by ID
        fetch_response = self.index.fetch(ids=[document_id])
        # Handle both dict and object responses
        vectors = fetch_response.vectors if hasattr(fetch_response, 'vectors') else fetch_response.get('vectors', {})
        if document_id not in vectors:
            return None

        vector_data = vectors[document_id]
        # Handle both dict and object vector data
        if isinstance(vector_data, dict):
            vector_values = vector_data.get('values', [])
            vector_metadata = vector_data.get('metadata', {})
        else:
            vector_values = vector_data.values if hasattr(vector_data, 'values') else []
            vector_metadata = vector_data.metadata if hasattr(vector_data, 'metadata') else {}
        
        metadata = vector_metadata or {}

        return Document(
            id=document_id,
            text=metadata.get("text", ""),
            embedding=vector_values,
            metadata={k: v for k, v in metadata.items() if k not in ("text", "doc_hash")},
            doc_hash=metadata.get("doc_hash"),
        )

    async def update_document(self, document: Document) -> None:
        """Update document in Pinecone (upsert)."""
        await self.add_documents([document])

    async def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics."""
        if self.index is None:
            await self.initialize()

        if self.index is None:
            return {"backend": self.backend.value}

        stats = self.index.describe_index_stats()
        # Handle both dict and object responses
        if isinstance(stats, dict):
            total_vectors = stats.get('total_vector_count', 0)
            dimension = stats.get('dimension', 0)
            index_fullness = stats.get('index_fullness', 0.0)
        else:
            total_vectors = stats.total_vector_count if hasattr(stats, 'total_vector_count') else 0
            dimension = stats.dimension if hasattr(stats, 'dimension') else 0
            index_fullness = stats.index_fullness if hasattr(stats, 'index_fullness') else 0.0
        
        return {
            "total_vectors": total_vectors,
            "dimension": dimension,
            "index_fullness": index_fullness,
            "backend": self.backend.value,
        }

    async def close(self) -> None:
        """Close Pinecone connection."""
        # Pinecone client doesn't need explicit closing
        pass

