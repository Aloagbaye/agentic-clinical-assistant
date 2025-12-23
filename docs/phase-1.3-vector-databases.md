# Phase 1.3: Vector Database Integration Layer

This document explains the vector database integration layer implementation completed in Phase 1.3.

## Overview

Phase 1.3 establishes a unified interface for working with multiple vector database backends (FAISS, Pinecone, and Weaviate), enabling flexible document storage and similarity search for the agentic clinical assistant system.

## Architecture

### Design Principles

1. **Unified Interface**: All backends implement the same `VectorDB` abstract interface
2. **Pluggable Backends**: Easy to switch or add new vector database backends
3. **Multi-Backend Support**: Query multiple backends simultaneously for comparison
4. **Retry Logic**: Automatic retries with exponential backoff for resilience
5. **Document Integrity**: SHA-256 hashing for document verification
6. **Metadata Filtering**: Support for filtering by document metadata

### Component Structure

```
vector/
├── base.py              # Abstract interface and models
├── faiss_adapter.py     # FAISS implementation
├── pinecone_adapter.py  # Pinecone implementation
├── weaviate_adapter.py  # Weaviate implementation
├── manager.py           # Unified manager with backend selection
├── embeddings.py        # Embedding generation utilities
└── README.md           # Module documentation
```

## Abstract Interface

### VectorDB Base Class

All vector database adapters implement the `VectorDB` abstract base class:

```python
class VectorDB(ABC):
    async def initialize() -> None
    async def add_documents(documents: List[Document]) -> List[str]
    async def search(query_embedding, top_k, filters) -> List[SearchResult]
    async def delete_documents(document_ids: List[str]) -> None
    async def get_document(document_id: str) -> Optional[Document]
    async def update_document(document: Document) -> None
    async def get_stats() -> Dict[str, Any]
    async def close() -> None
```

### Data Models

#### Document Model

```python
class Document(BaseModel):
    id: str                    # Unique document identifier
    text: str                  # Document text content
    embedding: Optional[List[float]]  # Vector embedding
    metadata: Dict[str, Any]   # Flexible metadata dictionary
    doc_hash: Optional[str]    # SHA-256 hash for verification
```

**Use Cases:**
- Store clinical policy documents
- Track document versions
- Store department/jurisdiction metadata
- Enable document integrity verification

#### SearchResult Model

```python
class SearchResult(BaseModel):
    document: Document  # The retrieved document
    score: float       # Similarity score (0-1, higher is better)
    doc_hash: str     # Document hash for verification
```

**Use Cases:**
- Return ranked search results
- Provide similarity scores for quality assessment
- Enable citation verification

## Backend Implementations

### 1. FAISS Adapter

**Type**: Local, in-memory or persisted to disk

**Features:**
- Fast similarity search using L2 distance
- Local persistence (saves index to disk)
- No external dependencies required
- Manual metadata filtering

**Implementation Details:**

```python
class FAISSAdapter(VectorDB):
    def __init__(self, index_path, dimension):
        self.index: faiss.IndexFlatL2  # L2 distance index
        self.documents: Dict[str, Document]  # Metadata storage
        self.id_to_index: Dict[str, int]  # ID mapping
```

**Persistence:**
- Saves FAISS index to `index.faiss`
- Saves metadata to `metadata.json`
- Automatically loads on initialization

**Limitations:**
- No built-in deletion (marks as deleted in metadata)
- Updates require delete + re-add
- Metadata filtering is manual (post-search)

**Best For:**
- Local development
- Self-hosted deployments
- Cost-sensitive scenarios
- Small to medium-scale deployments

### 2. Pinecone Adapter

**Type**: Managed cloud service

**Features:**
- Fully managed infrastructure
- Automatic scaling
- Built-in metadata filtering
- Cosine similarity search
- Batch operations

**Implementation Details:**

```python
class PineconeAdapter(VectorDB):
    def __init__(self, api_key, environment, index_name):
        self.pc: Pinecone  # Pinecone client
        self.index: Index  # Pinecone index
```

**Index Management:**
- Automatically creates index if it doesn't exist
- Uses cosine distance metric
- Serverless configuration (AWS/GCP)

**Metadata Filtering:**
- Native support via Pinecone filter expressions
- Supports equality and "in" operations
- Example: `{"department": "ER", "version": {"$in": ["1.0", "2.0"]}}`

**Best For:**
- Production deployments
- Teams without infrastructure expertise
- When you need automatic scaling
- High availability requirements

### 3. Weaviate Adapter

**Type**: Self-hosted or cloud-managed

**Features:**
- Hybrid search (vector + keyword)
- GraphQL API
- Rich metadata support
- Schema auto-creation
- Multiple distance metrics

**Implementation Details:**

```python
class WeaviateAdapter(VectorDB):
    def __init__(self, url, api_key, class_name):
        self.client: WeaviateClient  # Weaviate client
        self.class_name: str  # Collection name
```

**Search Modes:**

1. **Vector Search** (default):
   ```python
   results = await adapter.search(
       query_embedding=embedding,
       retrieval_mode="vector"
   )
   ```

2. **Hybrid Search** (vector + keyword):
   ```python
   results = await adapter.search(
       query_embedding=embedding,
       retrieval_mode="hybrid",
       query_text="sepsis treatment"
   )
   ```

3. **Keyword Search** (BM25):
   ```python
   results = await adapter.search(
       query_embedding=embedding,
       retrieval_mode="keyword",
       query_text="sepsis treatment"
   )
   ```

**Schema Management:**
- Automatically creates collection if it doesn't exist
- Defines properties: `text`, `doc_hash`, plus custom metadata
- Configures vector index with cosine distance

**Best For:**
- Complex queries requiring hybrid search
- Need for keyword matching alongside vector search
- Graph-like relationships between documents
- Rich metadata filtering requirements

## VectorDBManager

The `VectorDBManager` provides a unified interface for working with multiple backends.

### Features

1. **Backend Selection**: Choose specific backend or use default
2. **Multi-Backend Search**: Query all backends and merge results
3. **Automatic Retries**: Exponential backoff for transient failures
4. **Error Handling**: Graceful fallback between backends

### Usage

```python
from agentic_clinical_assistant.vector import VectorDBManager
from agentic_clinical_assistant.vector.base import VectorDBBackend

# Initialize manager
manager = VectorDBManager()
await manager.initialize(backends=[
    VectorDBBackend.FAISS,
    VectorDBBackend.PINECONE,
])

# Single backend search
results = await manager.search(
    query_embedding=embedding,
    top_k=10,
    backend=VectorDBBackend.FAISS,
)

# Multi-backend search (if enabled)
results = await manager.search(
    query_embedding=embedding,
    top_k=10,
    # backend=None uses multi-backend if enabled
)
```

### Multi-Backend Search

When `ENABLE_MULTI_BACKEND_RETRIEVAL=true`:

1. Queries all initialized backends in parallel
2. Merges results by document hash
3. Averages scores for documents found in multiple backends
4. Returns top-k results sorted by score

**Benefits:**
- Compare retrieval quality across backends
- Increase recall by combining results
- Identify backend-specific strengths

## Embedding Generation

### EmbeddingGenerator Class

Generates embeddings using sentence transformers:

```python
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator

generator = get_embedding_generator()

# Single embedding
embedding = generator.generate_embedding("Clinical policy text")

# Batch embeddings
embeddings = generator.generate_embeddings(
    texts=["text1", "text2", "text3"],
    batch_size=32
)

# Document hash
doc_hash = generator.compute_doc_hash("Clinical policy text")
```

### Features

- **Lazy Loading**: Model loads on first use
- **Batch Processing**: Efficient batch embedding generation
- **Dimension Detection**: Automatically detects embedding dimension
- **Document Hashing**: SHA-256 hash computation for integrity

### Configuration

```bash
# Embedding model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Device (cpu/cuda)
EMBEDDING_DEVICE=cpu
```

## Configuration

### Environment Variables

```bash
# Default backend selection
DEFAULT_VECTOR_BACKEND=faiss

# Multi-backend retrieval
ENABLE_MULTI_BACKEND_RETRIEVAL=false

# FAISS Configuration
FAISS_INDEX_PATH=./data/faiss_index
FAISS_DIMENSION=384

# Pinecone Configuration
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=clinical-assistant

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS_NAME=ClinicalDocument

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

## Usage Examples

### Basic Document Storage and Retrieval

```python
from agentic_clinical_assistant.vector import VectorDBManager
from agentic_clinical_assistant.vector.base import Document
from agentic_clinical_assistant.vector.embeddings import get_embedding_generator

# Initialize
manager = VectorDBManager()
await manager.initialize(backends=[VectorDBBackend.FAISS])

# Generate embeddings
generator = get_embedding_generator()
text = "Sepsis treatment requires immediate antibiotics administration..."
embedding = generator.generate_embedding(text)
doc_hash = generator.compute_doc_hash(text)

# Create document
doc = Document(
    id="policy_sepsis_v1",
    text=text,
    embedding=embedding,
    metadata={
        "department": "ER",
        "document_type": "policy",
        "version": "1.0",
        "effective_date": "2024-01-01",
    },
    doc_hash=doc_hash,
)

# Add document
await manager.add_documents([doc])

# Search
results = await manager.search(
    query_embedding=generator.generate_embedding("sepsis treatment"),
    top_k=5,
    filters={"department": "ER"},
)

# Process results
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Text: {result.document.text[:100]}...")
    print(f"Hash: {result.doc_hash}")
```

### Multi-Backend Comparison

```python
# Initialize multiple backends
await manager.initialize(backends=[
    VectorDBBackend.FAISS,
    VectorDBBackend.PINECONE,
])

# Search with each backend
faiss_results = await manager.search(
    query_embedding=embedding,
    top_k=10,
    backend=VectorDBBackend.FAISS,
)

pinecone_results = await manager.search(
    query_embedding=embedding,
    top_k=10,
    backend=VectorDBBackend.PINECONE,
)

# Compare results
print(f"FAISS found {len(faiss_results)} results")
print(f"Pinecone found {len(pinecone_results)} results")

# Check agreement
faiss_hashes = {r.doc_hash for r in faiss_results}
pinecone_hashes = {r.doc_hash for r in pinecone_results}
agreement = len(faiss_hashes & pinecone_hashes) / len(faiss_hashes | pinecone_hashes)
print(f"Agreement: {agreement:.2%}")
```

### Hybrid Search with Weaviate

```python
from agentic_clinical_assistant.vector import WeaviateAdapter

adapter = WeaviateAdapter()
await adapter.initialize()

# Hybrid search (combines vector and keyword)
results = await adapter.search(
    query_embedding=embedding,
    top_k=10,
    retrieval_mode="hybrid",
    query_text="sepsis treatment protocol",
    filters={"department": "ER"},
)
```

## Error Handling and Retries

All operations use `tenacity` for automatic retries:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def search(...):
    # Retries up to 3 times with exponential backoff
    # Waits: 2s, 4s, 8s between retries
```

**Retry Strategy:**
- **Max Attempts**: 3
- **Backoff**: Exponential (2s, 4s, 8s)
- **Handles**: Network errors, transient failures

## Performance Considerations

### Batch Operations

Use batch operations for better performance:

```python
# Add multiple documents efficiently
documents = [doc1, doc2, doc3, ...]
await manager.add_documents(documents, batch_size=100)
```

### Embedding Generation

Batch embedding generation is more efficient:

```python
# Batch is faster than individual calls
texts = ["text1", "text2", "text3", ...]
embeddings = generator.generate_embeddings(texts, batch_size=32)
```

### Connection Management

- **FAISS**: No connection overhead (local)
- **Pinecone**: Connection pooling handled by SDK
- **Weaviate**: Persistent connection, reuse client

## Backend Comparison Guide

### When to Use FAISS

✅ **Use FAISS when:**
- Local development and testing
- Self-hosted deployments
- Cost-sensitive scenarios
- Small to medium-scale (< 1M documents)
- Need full control over infrastructure

❌ **Avoid FAISS when:**
- Need automatic scaling
- Require built-in metadata filtering
- Need high availability
- Large-scale deployments (> 1M documents)

### When to Use Pinecone

✅ **Use Pinecone when:**
- Production deployments requiring high availability
- Teams without infrastructure expertise
- Need automatic scaling
- Want managed service benefits
- Budget allows for managed service costs

❌ **Avoid Pinecone when:**
- Cost-sensitive scenarios
- Offline/air-gapped environments
- Need full infrastructure control
- Very small deployments (< 10K documents)

### When to Use Weaviate

✅ **Use Weaviate when:**
- Need hybrid search (vector + keyword)
- Complex queries requiring keyword matching
- Self-hosted deployments with infrastructure team
- Need graph-like relationships
- Rich metadata filtering requirements

❌ **Avoid Weaviate when:**
- Simple vector-only search needs
- No infrastructure team available
- Want fully managed service
- Very simple use cases

## Integration with Agents

The vector database layer integrates with agents as follows:

1. **Retrieval Agent**: Uses `VectorDBManager` to search for evidence
2. **Document Ingestion**: Uses adapters to store policy documents
3. **Citation Verification**: Uses document hashes to verify sources
4. **Backend Selection**: Agent selects backend based on query type

Example integration:

```python
from agentic_clinical_assistant.vector import VectorDBManager

class RetrievalAgent:
    def __init__(self):
        self.vector_db = VectorDBManager()
        await self.vector_db.initialize()
    
    async def retrieve_evidence(self, query: str, filters: dict):
        # Generate query embedding
        embedding = generator.generate_embedding(query)
        
        # Search vector database
        results = await self.vector_db.search(
            query_embedding=embedding,
            top_k=10,
            filters=filters,
        )
        
        return results
```

## Testing

### Unit Tests

Test each adapter independently:

```python
@pytest.mark.asyncio
async def test_faiss_adapter():
    adapter = FAISSAdapter()
    await adapter.initialize()
    
    # Test add, search, delete operations
    ...
```

### Integration Tests

Test manager with multiple backends:

```python
@pytest.mark.asyncio
async def test_multi_backend_search():
    manager = VectorDBManager()
    await manager.initialize(backends=[
        VectorDBBackend.FAISS,
        VectorDBBackend.PINECONE,
    ])
    
    # Test multi-backend search
    ...
```

## Troubleshooting

### Common Issues

**FAISS Index Not Found:**
- Ensure `FAISS_INDEX_PATH` directory exists
- Check file permissions
- Verify index was saved correctly

**Pinecone Connection Errors:**
- Verify API key is correct
- Check network connectivity
- Ensure index exists or can be created

**Weaviate Connection Refused:**
- Verify Weaviate server is running
- Check URL and port
- Verify API key if using authentication

**Embedding Dimension Mismatch:**
- Ensure all documents use same embedding model
- Check `FAISS_DIMENSION` matches model dimension
- Verify embedding generation is consistent

### Performance Issues

**Slow Search:**
- Reduce `top_k` parameter
- Use batch operations for adds
- Consider indexing optimization

**High Memory Usage:**
- FAISS: Use smaller batch sizes
- Pinecone: Check index configuration
- Weaviate: Adjust collection settings

## Next Steps

After completing Phase 1.3, proceed to:

- **Phase 2.1**: Agent Orchestrator API
  - Implement FastAPI endpoints
  - Set up agent workflow engine
  - Create request/response models

- **Phase 3.2**: Retrieval Agent
  - Integrate with VectorDBManager
  - Implement evidence retrieval logic
  - Add backend selection policy

## Resources

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Sentence Transformers](https://www.sbert.net/)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)

