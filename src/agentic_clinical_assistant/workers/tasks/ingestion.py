"""Document ingestion tasks."""

import uuid
from typing import Any, Dict, List

from celery import Task

from agentic_clinical_assistant.database import get_async_session
from agentic_clinical_assistant.database.audit import AuditLogger
from agentic_clinical_assistant.vector import VectorDBManager
from agentic_clinical_assistant.vector.base import Document, VectorDBBackend
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator
from agentic_clinical_assistant.workers.celery_app import celery_app


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.ingestion.ingest_documents",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def ingest_documents(
    self,
    documents: List[Dict[str, Any]],
    backend: str = "faiss",
    batch_size: int = 100,
) -> Dict[str, Any]:
    """
    Ingest documents into vector database.

    Args:
        documents: List of documents with 'text' and optional 'metadata'
        backend: Vector backend to use
        batch_size: Batch size for processing

    Returns:
        Ingestion result with document IDs and hashes
    """
    try:
        # Initialize vector DB manager
        manager = VectorDBManager()
        # TODO: Initialize with proper backend
        # await manager.initialize(backends=[VectorDBBackend(backend)])

        # Get embedding generator
        generator = get_embedding_generator()

        # Process documents
        document_objects = []
        for doc_data in documents:
            text = doc_data.get("text", "")
            if not text:
                continue

            # Generate embedding
            embedding = generator.generate_embedding(text)
            doc_hash = generator.compute_doc_hash(text)

            # Create document object
            doc = Document(
                id=str(uuid.uuid4()),
                text=text,
                embedding=embedding,
                metadata=doc_data.get("metadata", {}),
                doc_hash=doc_hash,
            )
            document_objects.append(doc)

        # Add to vector database
        # TODO: Actually add documents (requires async context)
        # document_ids = await manager.add_documents(
        #     document_objects,
        #     backend=VectorDBBackend(backend),
        #     batch_size=batch_size,
        # )

        return {
            "ingested_count": len(document_objects),
            "document_ids": [doc.id for doc in document_objects],
            "doc_hashes": [doc.doc_hash for doc in document_objects],
        }

    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@celery_app.task(
    name="agentic_clinical_assistant.workers.tasks.ingestion.reindex_documents",
    bind=True,
    max_retries=2,
)
def reindex_documents(self, backend: str) -> Dict[str, Any]:
    """
    Reindex all documents in vector database.

    Args:
        backend: Vector backend to reindex

    Returns:
        Reindexing result
    """
    # TODO: Implement reindexing logic
    return {"status": "completed", "backend": backend}

