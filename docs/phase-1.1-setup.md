# Phase 1.1: Project Setup & Dependencies

This document explains the project setup completed in Phase 1.1, including the project structure, dependencies, and key technologies used.

## Overview

Phase 1.1 establishes the foundation for the agentic clinical assistant project. It sets up the Python project structure, dependency management, development tooling, and CI/CD pipeline.

## Project Structure

```
agentic-clinical-assistant/
├── src/
│   └── agentic_clinical_assistant/  # Main Python package
│       └── __init__.py
├── tests/                            # Test suite
│   ├── __init__.py
│   └── test_example.py
├── docs/                             # Documentation
│   └── phase-1.1-setup.md
├── scripts/                          # Utility scripts
│   ├── setup.sh                      # Unix/Mac setup
│   └── setup.ps1                     # Windows setup
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── pyproject.toml                    # Project config & dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore patterns
├── .pre-commit-config.yaml           # Pre-commit hooks config
├── Makefile                          # Development commands
└── README.md                         # Project documentation
```

## Dependency Management

### pyproject.toml

The project uses `pyproject.toml` (PEP 518/621) for modern Python packaging and dependency management. This file defines:

- **Project metadata**: Name, version, description, author
- **Dependencies**: All required packages for production
- **Optional dependencies**: Development tools (testing, linting, formatting)
- **Tool configurations**: Settings for black, ruff, isort, mypy, pytest

### Key Dependencies

#### API Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation using Python type annotations

#### Task Queue
- **Celery**: Distributed task queue for asynchronous job processing
- **Redis**: Message broker and result backend for Celery

#### Database
- **SQLAlchemy**: SQL toolkit and ORM
- **asyncpg**: Async PostgreSQL driver
- **Alembic**: Database migration tool
- **psycopg2-binary**: PostgreSQL adapter

#### Vector Databases

The project supports three vector database backends for storing and retrieving document embeddings:

##### FAISS (Facebook AI Similarity Search)
- **Type**: Local, in-memory or persisted to disk
- **Use Case**: Fast similarity search for large-scale vector databases
- **Pros**: 
  - Very fast for similarity search
  - No external service required
  - Can persist indices to disk
  - Free and open-source
- **Cons**: 
  - Requires managing storage and scaling
  - No built-in metadata filtering (requires custom implementation)
- **Best For**: Local development, self-hosted deployments, cost-sensitive scenarios

##### Pinecone
- **Type**: Managed cloud service
- **Use Case**: Production-ready vector database as a service
- **Pros**: 
  - Fully managed, no infrastructure to maintain
  - Built-in metadata filtering
  - Automatic scaling
  - High availability
  - Simple API
- **Cons**: 
  - Cost (pay-per-use model)
  - Requires internet connection
  - Vendor lock-in
- **Best For**: Production deployments, teams without infrastructure expertise

##### Weaviate
- **Type**: Self-hosted or cloud-managed
- **Use Case**: Vector database with graph-like capabilities
- **Pros**: 
  - Hybrid search (vector + keyword)
  - GraphQL API
  - Built-in vectorization (can generate embeddings)
  - Rich metadata support
  - Open-source with managed option
- **Cons**: 
  - More complex setup than Pinecone
  - Requires infrastructure management (if self-hosted)
- **Best For**: Complex queries requiring hybrid search, graph-like relationships

#### LLM SDKs
- **OpenAI**: Access to GPT models
- **Anthropic**: Access to Claude models

#### Monitoring
- **prometheus-client**: Metrics collection for Prometheus
- **structlog**: Structured logging

## Configuration Files

### YAML Configuration Files

YAML (YAML Ain't Markup Language) is a human-readable data serialization format used for configuration files. The project uses YAML for several configuration files:

#### .pre-commit-config.yaml

Pre-commit hooks configuration that runs automated checks before code is committed:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
```

**Key Hooks:**
- **black**: Code formatter (ensures consistent code style)
- **ruff**: Fast Python linter (catches errors and style issues)
- **isort**: Import sorter (organizes import statements)
- **mypy**: Static type checker (finds type errors)
- **pre-commit-hooks**: General file checks (trailing whitespace, YAML validation, etc.)

**Benefits:**
- Catches issues before code review
- Ensures consistent code style across the team
- Prevents common mistakes (merge conflicts, large files, etc.)

#### .github/workflows/ci.yml

GitHub Actions CI/CD pipeline configuration:

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

**Pipeline Stages:**
1. **Lint**: Checks code formatting and style
2. **Test**: Runs test suite across Python 3.10, 3.11, 3.12
3. **Security**: Runs safety and bandit security checks

**Benefits:**
- Automated testing on every push/PR
- Catches issues early in development
- Ensures code works across Python versions
- Security vulnerability scanning

### Environment Configuration (.env.example)

The `.env.example` file serves as a template for environment variables. Key configuration sections:

#### Application Settings
```bash
APP_NAME=agentic-clinical-assistant
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

#### Database Configuration
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_assistant
```

#### Vector Database Selection
```bash
DEFAULT_VECTOR_BACKEND=faiss  # Options: faiss, pinecone, weaviate
ENABLE_MULTI_BACKEND_RETRIEVAL=false
```

#### Vector DB Specific Settings

**FAISS:**
```bash
FAISS_INDEX_PATH=./data/faiss_index
FAISS_DIMENSION=384
```

**Pinecone:**
```bash
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=clinical-assistant
```

**Weaviate:**
```bash
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
WEAVIATE_CLASS_NAME=ClinicalDocument
```

#### Safety & Compliance
```bash
ENABLE_PHI_REDACTION=true
ENABLE_GROUNDING_VERIFICATION=true
ENABLE_PROMPT_INJECTION_DETECTION=true
```

## Development Tools

### Code Quality Tools

#### Black (Code Formatter)
- Automatically formats Python code
- Ensures consistent style across the project
- Configured in `pyproject.toml` with 100 character line length

#### Ruff (Linter)
- Fast Python linter written in Rust
- Replaces multiple tools (flake8, isort, etc.)
- Catches errors, style issues, and potential bugs

#### MyPy (Type Checker)
- Static type checking for Python
- Helps catch type-related errors before runtime
- Improves code maintainability

#### Pytest (Testing Framework)
- Modern Python testing framework
- Supports fixtures, parametrization, and async testing
- Configured with coverage reporting

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure:
- Code is properly formatted
- No linting errors
- Imports are sorted
- Type checks pass
- No large files or merge conflicts

**Installation:**
```bash
pre-commit install
```

**Manual Run:**
```bash
pre-commit run --all-files
```

## Makefile Commands

The `Makefile` provides convenient shortcuts for common development tasks:

```bash
make install          # Install production dependencies
make install-dev      # Install development dependencies
make test             # Run tests with coverage
make lint             # Run all linters
make format           # Format code with black and isort
make type-check       # Run mypy type checker
make clean            # Remove build artifacts
make run-api          # Start the FastAPI server
make run-worker       # Start the Celery worker
make migrate          # Run database migrations
```

## Setup Instructions

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentic-clinical-assistant
   ```

2. **Run setup script**
   - Windows: `.\scripts\setup.ps1`
   - Unix/Mac: `bash scripts/setup.sh`

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Manual Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file
   ```

## Vector Database Selection Guide

### When to Use FAISS
- Local development and testing
- Self-hosted deployments
- Cost-sensitive scenarios
- When you need full control over the infrastructure
- Small to medium-scale deployments

### When to Use Pinecone
- Production deployments requiring high availability
- Teams without infrastructure expertise
- When you need automatic scaling
- When you want to focus on application logic, not infrastructure
- Budget allows for managed service costs

### When to Use Weaviate
- Complex queries requiring hybrid search (vector + keyword)
- Need for graph-like relationships between documents
- Self-hosted deployments with infrastructure team
- When you need built-in vectorization
- Rich metadata filtering requirements

### Multi-Backend Strategy

The system supports querying multiple backends simultaneously for comparison:
- Compare retrieval quality across backends
- Select best backend per query type
- A/B testing and performance benchmarking
- Fallback options for high availability

## Next Steps

After completing Phase 1.1, you're ready to proceed to:

- **Phase 1.2**: Database Schema & Audit Layer
  - Design PostgreSQL schema
  - Set up Alembic migrations
  - Implement audit logging

- **Phase 1.3**: Vector Database Integration Layer
  - Implement FAISS adapter
  - Implement Pinecone adapter
  - Implement Weaviate adapter
  - Create unified interface

## Troubleshooting

### Common Issues

**Import errors after installation:**
- Ensure virtual environment is activated
- Reinstall: `pip install -e ".[dev]"`

**Pre-commit hooks failing:**
- Run manually to see errors: `pre-commit run --all-files`
- Fix formatting: `make format`

**Vector DB connection issues:**
- Check `.env` file has correct credentials
- Verify network connectivity (for Pinecone/Weaviate cloud)
- Check service is running (for local Weaviate)

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Black Code Style](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

