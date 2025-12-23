"""Vector database integration layer."""

from agentic_clinical_assistant.vector.base import VectorDB, VectorDBBackend
from agentic_clinical_assistant.vector.faiss_adapter import FAISSAdapter
from agentic_clinical_assistant.vector.pinecone_adapter import PineconeAdapter
from agentic_clinical_assistant.vector.weaviate_adapter import WeaviateAdapter
from agentic_clinical_assistant.vector.manager import VectorDBManager

__all__ = [
    "VectorDB",
    "VectorDBBackend",
    "FAISSAdapter",
    "PineconeAdapter",
    "WeaviateAdapter",
    "VectorDBManager",
]

