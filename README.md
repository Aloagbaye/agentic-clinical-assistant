# Agentic Clinical Assistant

PHI-Safe Clinical Ops Copilot (Agentic RAG System)

A production-ready, regulated-domain-safe agentic RAG system that orchestrates multiple specialized agents to provide clinical operations guidance with strict safety, grounding, and auditability requirements.

## Overview

Instead of a simple "question → retrieve → answer" flow, this system implements:

- **Planner** that decides what steps to take
- **Specialized agents/tools** that execute those steps
- **Verifier** that blocks unsafe or unsupported outputs
- **Traceable workflow** that logs everything for audit

The system generates final answers as the result of a controlled multi-step workflow.

## Features

- 🏥 **Multi-Agent Architecture**: Intake, Retrieval, Synthesis, and Verifier agents
- 🔒 **PHI-Safe**: Built-in PHI/PII redaction and safety checks
- 📊 **Multi-Backend Vector Search**: FAISS, Pinecone, and Weaviate support
- 🔍 **Evidence Grounding**: Every claim must be backed by citations
- 📈 **Observability**: Prometheus metrics and Grafana dashboards
- 🐳 **Production-Ready**: Kubernetes deployment with CI/CD

## Project Structure

```
agentic-clinical-assistant/
├── src/
│   └── agentic_clinical_assistant/  # Main package
├── tests/                            # Test suite
├── docs/                             # Documentation
├── scripts/                          # Utility scripts
├── pyproject.toml                    # Project configuration
├── .env.example                      # Environment variables template
└── README.md                         # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis (for Celery)
- (Optional) Docker and Docker Compose

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-clinical-assistant.git
   cd agentic-clinical-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Option 1: Using pyproject.toml (recommended)
   pip install -e ".[dev]"
   
   # Option 2: Using requirements files
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```

### Running the Application

1. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker Compose (if available)
   docker-compose up -d postgres redis
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Start the API server**
   ```bash
   uvicorn agentic_clinical_assistant.api.main:app --reload
   ```

4. **Start Celery worker** (in a separate terminal)
   ```bash
   celery -A agentic_clinical_assistant.workers.celery_app worker --loglevel=info
   ```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentic_clinical_assistant --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. Install them with:

```bash
pre-commit install
```

Hooks will run automatically on commit, checking:
- Code formatting (black)
- Linting (ruff)
- Import sorting (isort)
- Type checking (mypy)

## Configuration

See `.env.example` for all available configuration options. Key settings include:

- **Database**: PostgreSQL connection string
- **Vector DBs**: FAISS, Pinecone, or Weaviate configuration
- **LLM APIs**: OpenAI and Anthropic API keys
- **Safety**: PHI redaction and grounding verification settings

## Documentation

- **[Phase 1.1 Setup Guide](docs/phase-1.1-setup.md)**: Detailed explanation of project setup, dependencies, and configuration
- **[Phase 1.2 Database Schema](docs/phase-1.2-database.md)**: Database schema, models, migrations, and audit logging
- **[Phase 1.3 Vector Databases](docs/phase-1.3-vector-databases.md)**: Vector database integration layer with FAISS, Pinecone, and Weaviate
- **[Phase 2 Tutorial](docs/phase-2-tutorial.md)**: Complete guide to Agent Orchestrator API and Worker Infrastructure
- **[Project Outline](PROJECT_OUTLINE.md)**: Complete project roadmap and development phases

## Architecture

See [PROJECT_OUTLINE.md](PROJECT_OUTLINE.md) for detailed architecture and development phases.

### Core Components

1. **Agent Orchestrator API** (FastAPI)
   - `/agent/run` - Main entrypoint
   - `/agent/status/{run_id}` - Status tracking
   - `/metrics` - Prometheus metrics

2. **Specialized Agents**
   - Intake Agent: Policy & risk classification
   - Retrieval Agent: Evidence finder with multi-backend support
   - Synthesis Agent: Draft answer writer
   - Verifier Agent: Safety & grounding gatekeeper

3. **Vector Layer** (pluggable)
   - FAISS (local + persisted)
   - Pinecone (managed)
   - Weaviate (self-hosted)

4. **PostgreSQL**
   - Audit logs
   - Run traces
   - Citations and evaluations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && black src tests && ruff check src tests`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security & Compliance

⚠️ **Important**: This system handles clinical operations data. Ensure:

- PHI/PII is never stored in memory or logs
- All agent decisions are logged and traceable
- The system can abstain from unsafe requests
- Regular security audits are performed

## Status

🚧 **In Development** - See [PROJECT_OUTLINE.md](PROJECT_OUTLINE.md) for current phase and roadmap.

## Support

For issues and questions, please open an issue on GitHub.
