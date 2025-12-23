"""Embedding generation utilities."""

import hashlib
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from agentic_clinical_assistant.config import settings


class EmbeddingGenerator:
    """Generate embeddings for text documents."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize embedding generator.

        Args:
            model_name: Name of the sentence transformer model
            device: Device to use ('cpu' or 'cuda')
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        self.model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

    def _load_model(self) -> None:
        """Lazy load the embedding model."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name, device=self.device)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        self._load_model()
        if self.model is None:
            raise RuntimeError("Model not loaded")
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        self._load_model()
        if self.model is None:
            raise RuntimeError("Model not loaded")
        embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if self._dimension is None:
            self._load_model()
            if self.model is None:
                raise RuntimeError("Model not loaded")
            # Get dimension by encoding a dummy text
            dummy_embedding = self.model.encode("test", convert_to_numpy=True)
            self._dimension = len(dummy_embedding)
        return self._dimension

    def compute_doc_hash(self, text: str) -> str:
        """
        Compute SHA-256 hash of document text.

        Args:
            text: Document text

        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Global embedding generator instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get or create the global embedding generator."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator

