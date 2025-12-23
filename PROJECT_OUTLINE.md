# PROJECT_OUTLINE.md
## PHI-Safe Clinical Ops Copilot (Agentic RAG System)

### Project Vision
Build a production-ready, regulated-domain-safe agentic RAG system that orchestrates multiple specialized agents to provide clinical operations guidance with strict safety, grounding, and auditability requirements.

---

## Phase 1: Foundation & Core Infrastructure

### 1.1 Project Setup & Dependencies
**Tasks:**
- [ ] Initialize Python project structure with proper packaging
- [ ] Set up dependency management (requirements.txt / poetry / pipenv)
- [ ] Configure development environment (pre-commit hooks, linting, formatting)
- [ ] Set up version control structure (gitignore, branch strategy)
- [ ] Create initial project documentation structure

**Dependencies:**
- FastAPI (API framework)
- Celery/RQ/Arq (task queue)
- PostgreSQL client (psycopg2/asyncpg)
- Vector DB clients (FAISS, Pinecone, Weaviate)
- LLM SDKs (OpenAI/Anthropic/etc.)
- Monitoring libraries (Prometheus client)

**Deliverables:**
- Project structure with src/ directory
- requirements.txt or pyproject.toml
- .env.example template
- Basic CI/CD configuration (GitHub Actions / Jenkins)

---

### 1.2 Database Schema & Audit Layer
**Tasks:**
- [ ] Design PostgreSQL schema for:
  - Agent run logs (run_id, status, timestamps, user_id)
  - Tool call records (tool_name, inputs, outputs, duration, backend)
  - Evidence retrieval logs (query, backend, top_k, scores, doc_hashes)
  - Prompt versions (version_id, template, model, parameters)
  - Citations and grounding verification results
  - Evaluation outcomes (benchmark_id, metrics, backend)
- [ ] Create Alembic migrations
- [ ] Implement audit logging utilities
- [ ] Set up database connection pooling

**Deliverables:**
- Database schema SQL/migrations
- ORM models (SQLAlchemy)
- Audit logging service
- Database initialization scripts

---

### 1.3 Vector Database Integration Layer
**Tasks:**
- [ ] Implement abstract VectorDB interface
- [ ] FAISS adapter (local + persisted volume)
  - Embedding generation
  - Index creation and persistence
  - Similarity search with metadata filtering
- [ ] Pinecone adapter
  - Connection management
  - Index operations
  - Query with filters
- [ ] Weaviate adapter
  - Schema management
  - Hybrid search support
  - GraphQL queries
- [ ] Unified query interface with backend selection
- [ ] Connection pooling and retry logic

**Deliverables:**
- `src/vector/` module with adapters
- Configuration for multiple backends
- Integration tests for each backend
- Performance benchmarking utilities

---

## Phase 2: Agent Orchestration Framework

### 2.1 Agent Orchestrator API (FastAPI)
**Tasks:**
- [ ] Design API schema (request/response models)
- [ ] Implement `/agent/run` endpoint
  - Request validation
  - Run ID generation
  - Agent workflow initiation
  - Async task dispatch
- [ ] Implement `/agent/status/{run_id}` endpoint
  - Status tracking
  - Progress reporting
  - Error retrieval
- [ ] Implement `/tools/*` internal endpoints (optional)
- [ ] Implement `/metrics` endpoint (Prometheus format)
- [ ] Add request/response logging middleware
- [ ] Implement rate limiting and authentication

**Deliverables:**
- FastAPI application with all endpoints
- OpenAPI/Swagger documentation
- Request/response models (Pydantic)
- API integration tests

---

### 2.2 Tool Worker Infrastructure
**Tasks:**
- [ ] Set up Celery/RQ/Arq worker configuration
- [ ] Design task queue structure
- [ ] Implement task routing and priority queues
- [ ] Create worker health check endpoints
- [ ] Set up task result backend (Redis/RabbitMQ)
- [ ] Implement task retry and error handling

**Deliverables:**
- Worker configuration files
- Task definitions
- Worker deployment scripts
- Monitoring integration

---

### 2.3 Agent Workflow Engine
**Tasks:**
- [ ] Design workflow state machine
- [ ] Implement agent execution pipeline:
  1. Intake Agent → RequestPlan
  2. Retrieval Agent → Evidence bundles
  3. Synthesis Agent → Draft answer
  4. Verifier Agent → Approved answer
- [ ] Implement workflow orchestration logic
- [ ] Add step-by-step logging and tracing
- [ ] Implement error handling and rollback
- [ ] Add workflow visualization/debugging tools

**Deliverables:**
- Workflow engine core
- Agent execution framework
- State management system
- Workflow tests

---

## Phase 3: Specialized Agents Implementation

### 3.1 Intake Agent (Policy & Risk Classification)
**Tasks:**
- [ ] Implement request classification logic:
  - "Policy lookup"
  - "Summarize guideline"
  - "Compare protocols"
  - "Explain policy step-by-step"
- [ ] Build risk detection:
  - Diagnosis/treatment scope validation
  - Unsupported request detection
- [ ] Extract constraints:
  - Jurisdiction parsing
  - Department identification
  - Document version requirements
  - Timeframe extraction
- [ ] Generate RequestPlan output:
  - Risk label (low/medium/high)
  - Required tools list
  - Query type classification
- [ ] Add logging for classification decisions

**Deliverables:**
- Intake agent module
- Classification models/prompts
- RequestPlan schema
- Unit tests with various request types

---

### 3.2 Retrieval Agent (Evidence Finder)
**Tasks:**
- [ ] Implement multi-backend retrieval:
  - Query all configured backends (FAISS/Pinecone/Weaviate)
  - OR query default backend based on policy
- [ ] Apply metadata filters:
  - Department filtering
  - Document type filtering
  - Effective date range filtering
- [ ] Implement hybrid search (Weaviate)
- [ ] Backend selection policy:
  - Highest mean score
  - Lowest latency (p95 SLA)
  - Highest historical nDCG for query class
- [ ] Compute agreement scores between backends
- [ ] Generate evidence bundles with:
  - Top-k results per backend
  - Scores and confidence
  - Document hashes for verification
  - Retrieval mode logging

**Deliverables:**
- Retrieval agent module
- Backend selection logic
- Evidence bundle schema
- Retrieval benchmarking integration

---

### 3.3 Synthesis Agent (Draft Answer Writer)
**Tasks:**
- [ ] Design constrained answer template:
  - Summary section
  - Procedure steps
  - Exceptions/edge cases
  - Citations section
- [ ] Implement evidence-to-answer generation:
  - LLM integration with constrained prompting
  - Claim extraction
  - Citation mapping (claim → source)
- [ ] Enforce citation requirements:
  - Every major claim must have citation
  - Citation format standardization
- [ ] Generate draft answer with metadata:
  - Claim-to-citation mapping
  - Confidence scores
  - Evidence sources used

**Deliverables:**
- Synthesis agent module
- Prompt templates (versioned)
- Citation mapping utilities
- Answer generation tests

---

### 3.4 Verifier Agent (Safety + Grounding Gatekeeper)
**Tasks:**
- [ ] Implement PHI/PII redaction checks:
  - Regex-based detection
  - Optional NER pass
  - Redaction hit counting
- [ ] Build prompt injection resistance:
  - Detect instructions within documents
  - Ignore embedded commands
- [ ] Implement evidence grounding verification:
  - Map each claim to citation
  - Validate citation exists and supports claim
  - Remove unsupported claims or abstain
- [ ] Build refusal policy:
  - Detect unsafe requests
  - Generate safe abstention messages
  - Suggest follow-up questions
- [ ] Generate verification report:
  - Pass/fail status
  - Reasons for failures
  - Redaction events
  - Grounding gaps

**Deliverables:**
- Verifier agent module
- PHI redaction tool
- Grounding verification logic
- Safety policy engine
- Comprehensive test suite

---

### 3.5 Routing Agent (Optional)
**Tasks:**
- [ ] Implement vague question detection
- [ ] Generate clarifying questions
- [ ] Trigger "Document ingestion needed" flow
- [ ] Route to appropriate agent based on question type

**Deliverables:**
- Routing agent module
- Question classification logic
- Clarification generation

---

## Phase 4: Tools Implementation

### 4.1 Core Tools
**Tasks:**
- [ ] Implement `retrieve_evidence(query, backend, filters, top_k)`
  - Backend selection
  - Filter application
  - Result formatting with citations
  - Doc hash generation
- [ ] Implement `redact_phi(text)`
  - Regex patterns for PHI
  - NER integration (optional)
  - Redaction counting
  - Logging
- [ ] Implement `run_backend_benchmark(eval_set_id)`
  - Load evaluation dataset
  - Run queries against all backends
  - Compute metrics (MRR, nDCG, Recall@k)
  - Store results in Postgres
- [ ] Implement `generate_answer(evidence_bundle, prompt_version, model)`
  - Constrained generation
  - Template application
  - Claim/citation mapping
- [ ] Implement `verify_grounding(draft, evidence_bundle)`
  - Claim extraction
  - Citation validation
  - Pass/fail determination
  - Reason generation

**Deliverables:**
- Tool implementations in `src/tools/`
- Tool call logging integration
- Unit tests for each tool
- Tool documentation

---

### 4.2 Workflow Mode Tools
**Tasks:**
- [ ] Implement Checklist Builder tool:
  - Parse procedure steps from answer
  - Generate structured checklist JSON
  - Support UI integration format
- [ ] Implement Workflow Action tools:
  - Step-by-step procedure extraction
  - Structured output generation
  - Multi-format support (JSON, Markdown, HTML)

**Deliverables:**
- Workflow tools module
- Structured output generators
- Integration examples

---

## Phase 5: Agent Memory System

### 5.1 Session Memory
**Tasks:**
- [ ] Design session memory schema:
  - User preferences storage
  - Session expiration logic
  - Preference types (display format, jurisdiction, department)
- [ ] Implement session management:
  - Create/update/retrieve sessions
  - Expiration handling
  - Preference application to queries
- [ ] Add memory to agent workflow:
  - Load user preferences at intake
  - Apply preferences to retrieval
  - Store updated preferences

**Deliverables:**
- Session memory service
- Database schema for sessions
- Integration with agents

---

### 5.2 Policy Memory
**Tasks:**
- [ ] Design policy memory schema:
  - Frequently used documents
  - Successful query patterns
  - Policy aliases mapping
- [ ] Implement memory operations:
  - Document usage tracking
  - Query pattern learning
  - Alias resolution
- [ ] Ensure NO patient data storage
- [ ] Add memory retrieval to agents

**Deliverables:**
- Policy memory service
- Database schema
- Memory learning algorithms
- Alias resolution system

---

## Phase 6: Observability & Monitoring

### 6.1 Prometheus Metrics
**Tasks:**
- [ ] Implement agent run metrics:
  - `agent_runs_total{status}`
  - `agent_step_latency_ms{step}` (intake/retrieve/synthesize/verify)
  - `tool_calls_total{tool_name,backend}`
- [ ] Implement safety & grounding metrics:
  - `grounding_fail_total{reason}`
  - `answers_abstained_total{reason}`
  - `citationless_answer_total`
  - `phi_redaction_events_total`
- [ ] Implement backend comparison metrics:
  - `retrieval_mrr{backend}`
  - `retrieval_ndcg{backend}`
  - `retrieval_latency_ms{backend}`
  - `backend_selected_total{backend,query_type}`
- [ ] Add metric collection to all agents and tools
- [ ] Expose `/metrics` endpoint

**Deliverables:**
- Prometheus client integration
- Metric definitions
- Metric collection throughout codebase
- Metrics documentation

---

### 6.2 Grafana Dashboards
**Tasks:**
- [ ] Create dashboard: "Agent Performance"
  - Run counts and status breakdown
  - Step latency (p50, p95, p99)
  - Tool call distribution
- [ ] Create dashboard: "Safety & Quality"
  - Grounding failure reasons
  - Abstention rates
  - Citation coverage
  - PHI redaction events
- [ ] Create dashboard: "Backend Comparison"
  - MRR/nDCG/Recall by backend
  - Latency comparison
  - Backend selection patterns
  - Query type performance
- [ ] Create dashboard: "SLA Health"
  - P95 latency per agent step
  - SLA compliance status
  - Error rates

**Deliverables:**
- Grafana dashboard JSON files
- Dashboard documentation
- Alert rules (optional)

---

### 6.3 Logging & Tracing (Optional)
**Tasks:**
- [ ] Set up structured logging (JSON format)
- [ ] Integrate Loki for log aggregation
- [ ] Set up distributed tracing (Tempo/Jaeger)
- [ ] Add trace IDs to all agent runs
- [ ] Create trace visualization

**Deliverables:**
- Logging configuration
- Tracing instrumentation
- Log aggregation setup

---

## Phase 7: CI/CD & Deployment

### 7.1 Jenkins Pipeline
**Tasks:**
- [ ] Create pipeline stages:
  1. Lint + unit tests (agents/tools/adapters)
  2. Integration tests (compose stack)
  3. Contract tests:
     - Same query returns same schema
     - Verifier blocks unsupported claims
  4. Build images (agent-api, worker)
  5. Push images to registry
  6. Deploy to K8s (dev)
  7. Smoke tests:
     - Run 10 agent queries
     - Ensure citations present
     - Ensure no PHI leakage in logs
- [ ] Set up nightly scheduled job:
  - Run eval harness
  - Publish results (Prometheus + Postgres)
- [ ] Add deployment notifications

**Deliverables:**
- Jenkinsfile
- Test suites (unit, integration, contract)
- Dockerfiles for all services
- Deployment scripts

---

### 7.2 Kubernetes Deployment
**Tasks:**
- [ ] Create K8s manifests:
  - Deployment: `agent-api`
  - Deployment: `worker`
  - StatefulSet: `weaviate`
  - StatefulSet: `postgres`
- [ ] Create ConfigMaps:
  - Backend selection policy
  - Agent configuration
- [ ] Create Secrets:
  - Model API keys
  - Database credentials
  - Vector DB credentials
- [ ] Set up Horizontal Pod Autoscaling (HPA):
  - Scale agent-api on RPS/CPU
  - Scale worker on queue depth
- [ ] Configure service discovery
- [ ] Set up ingress/load balancer
- [ ] Add resource limits and requests

**Deliverables:**
- K8s manifests (YAML files)
- Helm charts (optional)
- Deployment documentation
- Monitoring integration

---

### 7.3 Docker & Containerization
**Tasks:**
- [ ] Create Dockerfile for agent-api
- [ ] Create Dockerfile for worker
- [ ] Create docker-compose.yml for local development
- [ ] Set up multi-stage builds
- [ ] Optimize image sizes
- [ ] Add health checks

**Deliverables:**
- Dockerfiles
- docker-compose.yml
- .dockerignore files
- Container documentation

---

## Phase 8: Testing & Evaluation

### 8.1 Unit Testing
**Tasks:**
- [ ] Write unit tests for all agents
- [ ] Write unit tests for all tools
- [ ] Write unit tests for vector DB adapters
- [ ] Write unit tests for verification logic
- [ ] Achieve >80% code coverage

**Deliverables:**
- Test suite with pytest
- Coverage reports
- CI integration

---

### 8.2 Integration Testing
**Tasks:**
- [ ] Test full agent workflow end-to-end
- [ ] Test multi-backend retrieval
- [ ] Test error handling and recovery
- [ ] Test database operations
- [ ] Test API endpoints

**Deliverables:**
- Integration test suite
- Test fixtures and mocks
- CI integration

---

### 8.3 Evaluation Harness
**Tasks:**
- [ ] Create evaluation dataset:
  - Clinical policy questions
  - Expected answers
  - Ground truth citations
- [ ] Implement evaluation metrics:
  - Answer quality (BLEU, ROUGE, semantic similarity)
  - Citation accuracy
  - Grounding verification
  - Latency measurements
- [ ] Build evaluation runner:
  - Run against all backends
  - Compare results
  - Generate reports
- [ ] Integrate with nightly CI job

**Deliverables:**
- Evaluation dataset
- Evaluation framework
- Automated evaluation pipeline
- Evaluation reports

---

## Phase 9: Documentation & Production Readiness

### 9.1 API Documentation
**Tasks:**
- [ ] Complete OpenAPI/Swagger documentation
- [ ] Add request/response examples
- [ ] Document error codes and handling
- [ ] Create API usage guide

**Deliverables:**
- Complete API docs
- Usage examples
- Error handling guide

---

### 9.2 System Documentation
**Tasks:**
- [ ] Architecture documentation
- [ ] Agent design documentation
- [ ] Tool documentation
- [ ] Deployment guide
- [ ] Operations runbook
- [ ] Troubleshooting guide

**Deliverables:**
- Architecture diagrams
- System documentation
- Operations manual

---

### 9.3 Security & Compliance
**Tasks:**
- [ ] Security audit checklist
- [ ] PHI handling documentation
- [ ] Access control implementation
- [ ] Audit log review procedures
- [ ] Compliance documentation

**Deliverables:**
- Security documentation
- Compliance checklist
- Audit procedures

---

## Phase 10: Extensions & Enhancements

### 10.1 Workflow Mode Enhancements
**Tasks:**
- [ ] Expand structured output formats
- [ ] Add more workflow actions
- [ ] UI integration examples
- [ ] Workflow customization

**Deliverables:**
- Enhanced workflow tools
- Integration examples

---

### 10.2 Performance Optimization
**Tasks:**
- [ ] Caching layer for frequent queries
- [ ] Query optimization
- [ ] Database indexing optimization
- [ ] Vector search optimization
- [ ] Load testing and tuning

**Deliverables:**
- Performance improvements
- Benchmarking results
- Optimization documentation

---

## Project Milestones

### Milestone 1: Core Infrastructure (Phases 1-2)
- Foundation complete, API running, basic workflow

### Milestone 2: Agents & Tools (Phases 3-4)
- All agents implemented, tools functional

### Milestone 3: Memory & Monitoring (Phases 5-6)
- Memory system working, observability complete

### Milestone 4: Production Deployment (Phases 7-8)
- CI/CD working, deployed to K8s, tested

### Milestone 5: Documentation & Polish (Phases 9-10)
- Fully documented, production-ready

---

## Success Criteria

- [ ] All agents execute successfully in workflow
- [ ] Verifier blocks unsafe outputs
- [ ] All answers have proper citations
- [ ] PHI redaction works correctly
- [ ] Multi-backend retrieval functional
- [ ] Metrics and monitoring operational
- [ ] CI/CD pipeline working
- [ ] K8s deployment successful
- [ ] Evaluation harness shows quality metrics
- [ ] Documentation complete

---

## Technical Stack Summary

- **API Framework:** FastAPI
- **Task Queue:** Celery/RQ/Arq
- **Database:** PostgreSQL
- **Vector DBs:** FAISS, Pinecone, Weaviate
- **Monitoring:** Prometheus + Grafana
- **Logging:** Structured JSON logs (optional: Loki)
- **Tracing:** (optional: Tempo/Jaeger)
- **CI/CD:** Jenkins
- **Orchestration:** Kubernetes
- **Containerization:** Docker

---

## Notes

- This is a regulated domain system - safety and auditability are paramount
- All agent decisions must be logged and traceable
- Patient data (PHI/PII) must never be stored in memory or logs
- The system must be able to abstain from answering unsafe requests
- Backend selection should be data-driven based on measured performance
- The agentic approach enables dynamic, multi-step workflows while maintaining control

