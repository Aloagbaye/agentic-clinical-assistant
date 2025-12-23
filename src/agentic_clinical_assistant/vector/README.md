# Vector Database Integration Layer

This module provides a unified interface for working with multiple vector database backends: FAISS, Pinecone, and Weaviate.

## Architecture

### Abstract Interface

All vector database adapters implement the `VectorDB` abstract base class, which defines:

- `initialize()` - Set up connection/index
- `add_documents()` - Add documents with embeddings
- `search()` - Search for similar documents
- `delete_documents()` - Delete documents
- `get_document()` - Retrieve a single document
- `update_document()` - Update a document
- `get_stats()` - Get database statistics
- `close()` - Cleanup resources

### Supported Backends

1. **FAISS** - Local, fast similarity search
   - Pros: Fast, no external dependencies, free
   - Cons: No built-in metadata filtering, requires manual persistence
   - Best for: Local development, self-hosted deployments

2. **Pinecone** - Managed cloud service
   - Pros: Fully managed, automatic scaling, built-in filtering
   - Cons: Cost, requires internet connection
   - Best for: Production deployments

3. **Weaviate** - Self-hosted with hybrid search
   - Pros: Hybrid search (vector + keyword), GraphQL API
   - Cons: Requires infrastructure management
   - Best for: Complex queries, hybrid search needs

## Usage

### Basic Usage

```python
from agentic_clinical_assistant.vector import VectorDBManager
from agentic_clinical_assistant.vector.base import Document
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator

# Initialize manager
manager = VectorDBManager()
await manager.initialize(backends=[VectorDBBackend.FAISS])

# Generate embeddings
generator = get_embedding_generator()
text = "Clinical policy for sepsis treatment"
embedding = generator.generate_embedding(text)
doc_hash = generator.compute_doc_hash(text)

# Create document
doc = Document(
    id="doc1",
    text=text,
    embedding=embedding,
    metadata={"department": "ER", "version": "1.0"},
    doc_hash=doc_hash,
)

# Add document
await manager.add_documents([doc])

# Search
results = await manager.search(
    query_embedding=embedding,
    top_k=5,
    filters={"department": "ER"},
)

# Cleanup
await manager.close()
```

### Multi-Backend Search

```python
# Initialize multiple backends
await manager.initialize(backends=[
    VectorDBBackend.FAISS,
    VectorDBBackend.PINECONE,
    VectorDBBackend.WEAVIATE,
])

# Search across all backends (if enabled)
results = await manager.search(
    query_embedding=embedding,
    top_k=10,
    # backend=None means use multi-backend if enabled
)
```

### Backend-Specific Features

#### FAISS

```python
from agentic_clinical_assistant.vector import FAISSAdapter

adapter = FAISSAdapter(
    index_path="./data/faiss_index",
    dimension=384,
)
await adapter.initialize()
```

#### Pinecone

```python
from agentic_clinical_assistant.vector import PineconeAdapter

adapter = PineconeAdapter(
    api_key="your-api-key",
    environment="us-west1-gcp",
    index_name="clinical-assistant",
)
await adapter.initialize()
```

#### Weaviate (Hybrid Search)

```python
from agentic_clinical_assistant.vector import WeaviateAdapter

adapter = WeaviateAdapter(
    url="http://localhost:8080",
    class_name="ClinicalDocument",
)
await adapter.initialize()

# Hybrid search (vector + keyword)
results = await adapter.search(
    query_embedding=embedding,
    top_k=10,
    retrieval_mode="hybrid",
    query_text="sepsis treatment protocol",
)
```

## Configuration

Set in `.env`:

```bash
# Default backend
DEFAULT_VECTOR_BACKEND=faiss

# Enable multi-backend retrieval
ENABLE_MULTI_BACKEND_RETRIEVAL=false

# FAISS
FAISS_INDEX_PATH=./data/faiss_index
FAISS_DIMENSION=384

# Pinecone
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=clinical-assistant

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS_NAME=ClinicalDocument

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

## Document Model

```python
class Document(BaseModel):
    id: str                    # Unique document ID
    text: str                  # Document text content
    embedding: List[float]     # Vector embedding
    metadata: Dict[str, Any]  # Flexible metadata
    doc_hash: str             # SHA-256 hash for verification
```

## Search Results

```python
class SearchResult(BaseModel):
    document: Document  # The document
    score: float        # Similarity score (0-1)
    doc_hash: str      # Document hash for verification
```

## Error Handling

All operations use `tenacity` for automatic retries:

- 3 retry attempts
- Exponential backoff (2s, 4s, 8s)
- Handles transient network errors

## Performance Considerations

1. **Batch Operations**: Use `batch_size` parameter for bulk adds
2. **Connection Pooling**: Adapters manage their own connections
3. **Lazy Loading**: Embedding model loads on first use
4. **Caching**: Document metadata cached in FAISS adapter

## Next Steps

- Add integration tests for each backend
- Implement benchmarking utilities
- Add query optimization strategies
- Support for incremental indexing

