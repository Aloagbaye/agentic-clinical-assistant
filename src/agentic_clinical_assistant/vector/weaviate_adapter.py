"""Weaviate vector database adapter."""

from typing import Any, Dict, List, Optional

import weaviate
from weaviate.classes.query import MetadataQuery

from agentic_clinical_assistant.config import settings
from agentic_clinical_assistant.vector.base import Document, SearchResult, VectorDB, VectorDBBackend


class WeaviateAdapter(VectorDB):
    """Weaviate vector database adapter with hybrid search support."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        class_name: Optional[str] = None,
    ):
        """
        Initialize Weaviate adapter.

        Args:
            url: Weaviate server URL
            api_key: Weaviate API key (optional)
            class_name: Weaviate class name for documents
        """
        super().__init__(VectorDBBackend.WEAVIATE)
        self.url = url or settings.WEAVIATE_URL
        self.api_key = api_key or settings.WEAVIATE_API_KEY
        self.class_name = class_name or settings.WEAVIATE_CLASS_NAME
        self.client: Optional[weaviate.WeaviateClient] = None

    async def initialize(self) -> None:
        """Initialize Weaviate connection and create schema if needed."""
        # Create client
        if self.api_key:
            auth = weaviate.auth.AuthApiKey(api_key=self.api_key)
            self.client = weaviate.connect_to_custom(
                url=self.url,
                auth_credentials=auth,
            )
        else:
            self.client = weaviate.connect_to_local(url=self.url)

        # Get dimension
        from agentic_clinical_assistant.vector.embeddings import get_embedding_generator

        generator = get_embedding_generator()
        dimension = generator.dimension

        # Create schema if class doesn't exist
        if not self.client.collections.exists(self.class_name):
            self.client.collections.create(
                name=self.class_name,
                vectorizer_config=weaviate.classes.config.Configure.vectorizer.none(),
                vector_config=weaviate.classes.config.Configure.vector.index(
                    distance_metric=weaviate.classes.config.VectorDistances.COSINE
                ),
                properties=[
                    weaviate.classes.config.Property(
                        name="text",
                        data_type=weaviate.classes.config.DataType.TEXT,
                    ),
                    weaviate.classes.config.Property(
                        name="doc_hash",
                        data_type=weaviate.classes.config.DataType.TEXT,
                    ),
                ],
            )

    async def add_documents(
        self, documents: List[Document], batch_size: Optional[int] = None
    ) -> List[str]:
        """Add documents to Weaviate."""
        if self.client is None:
            await self.initialize()

        if self.client is None:
            raise RuntimeError("Weaviate client not initialized")

        collection = self.client.collections.get(self.class_name)
        document_ids = []

        batch_size = batch_size or 100

        # Prepare objects for Weaviate
        with collection.batch.dynamic() as batch:
            for doc in documents:
                if doc.embedding is None:
                    raise ValueError(f"Document {doc.id} missing embedding")

                # Weaviate object
                batch.add_object(
                    properties={
                        "text": doc.text,
                        "doc_hash": doc.doc_hash or "",
                        **doc.metadata,
                    },
                    vector=doc.embedding,
                    uuid=doc.id,
                )
                document_ids.append(doc.id)

        return document_ids

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        retrieval_mode: str = "vector",
        **kwargs: Any,
    ) -> List[SearchResult]:
        """
        Search for similar documents in Weaviate.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            filters: Metadata filters
            retrieval_mode: "vector", "hybrid", or "keyword"
            **kwargs: Additional parameters
        """
        if self.client is None:
            await self.initialize()

        if self.client is None:
            raise RuntimeError("Weaviate client not initialized")

        collection = self.client.collections.get(self.class_name)

        # Build where filter
        where_filter = None
        if filters:
            # Weaviate uses GraphQL-style filters
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(
                        {
                            "path": [key],
                            "operator": "ContainsAny",
                            "valueText": value,
                        }
                    )
                else:
                    conditions.append(
                        {
                            "path": [key],
                            "operator": "Equal",
                            "valueText": str(value),
                        }
                    )
            if conditions:
                where_filter = {"operator": "And", "operands": conditions}

        # Perform search based on mode
        if retrieval_mode == "hybrid":
            # Hybrid search (vector + keyword)
            response = collection.query.hybrid(
                query=kwargs.get("query_text", ""),
                vector=query_embedding,
                limit=top_k,
                where=where_filter,
                return_metadata=MetadataQuery(distance=True),
            )
        elif retrieval_mode == "keyword":
            # Keyword-only search
            response = collection.query.bm25(
                query=kwargs.get("query_text", ""),
                limit=top_k,
                where=where_filter,
                return_metadata=MetadataQuery(distance=True),
            )
        else:
            # Vector search (default)
            response = collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                where=where_filter,
                return_metadata=MetadataQuery(distance=True),
            )

        results = []
        for obj in response.objects:
            props = obj.properties
            doc = Document(
                id=str(obj.uuid),
                text=props.get("text", ""),
                metadata={k: v for k, v in props.items() if k not in ("text", "doc_hash")},
                doc_hash=props.get("doc_hash"),
            )

            # Convert distance to similarity score
            distance = obj.metadata.distance if obj.metadata.distance else 0.0
            score = max(0.0, 1.0 - float(distance))

            results.append(
                SearchResult(
                    document=doc,
                    score=score,
                    doc_hash=doc.doc_hash or "",
                )
            )

        return results

    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Weaviate."""
        if self.client is None:
            await self.initialize()

        if self.client is None:
            raise RuntimeError("Weaviate client not initialized")

        collection = self.client.collections.get(self.class_name)
        for doc_id in document_ids:
            try:
                collection.data.delete_by_id(doc_id)
            except Exception:
                # Ignore errors for non-existent documents
                pass

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID from Weaviate."""
        if self.client is None:
            await self.initialize()

        if self.client is None:
            raise RuntimeError("Weaviate client not initialized")

        collection = self.client.collections.get(self.class_name)
        try:
            obj = collection.data.get_by_id(doc_id)
            if obj is None:
                return None

            props = obj.properties
            return Document(
                id=str(obj.uuid),
                text=props.get("text", ""),
                metadata={k: v for k, v in props.items() if k not in ("text", "doc_hash")},
                doc_hash=props.get("doc_hash"),
            )
        except Exception:
            return None

    async def update_document(self, document: Document) -> None:
        """Update document in Weaviate."""
        # Delete and re-add
        await self.delete_documents([document.id])
        await self.add_documents([document])

    async def get_stats(self) -> Dict[str, Any]:
        """Get Weaviate collection statistics."""
        if self.client is None:
            await self.initialize()

        if self.client is None:
            return {"backend": self.backend.value}

        collection = self.client.collections.get(self.class_name)
        # Weaviate doesn't provide direct stats, so we count objects
        response = collection.query.fetch_objects(limit=1, return_metadata=MetadataQuery())
        # This is approximate - full count would require pagination
        return {
            "backend": self.backend.value,
            "class_name": self.class_name,
        }

    async def close(self) -> None:
        """Close Weaviate connection."""
        if self.client:
            self.client.close()

