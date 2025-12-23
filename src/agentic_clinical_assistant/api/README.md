# Agent Orchestrator API

FastAPI-based REST API for the agentic clinical assistant system.

## Endpoints

### Agent Endpoints

#### POST `/agent/run`

Initiate an agent run.

**Request:**
```json
{
  "request_text": "What is the policy for sepsis treatment?",
  "user_id": "user123",
  "metadata": {
    "department": "ER"
  }
}
```

**Response:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z",
  "message": "Agent run initiated successfully"
}
```

#### GET `/agent/status/{run_id}`

Get the status of an agent run.

**Response:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "request_text": "What is the policy for sepsis treatment?",
  "request_type": "policy_lookup",
  "risk_label": "low",
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:01Z",
  "completed_at": null,
  "final_answer": null,
  "progress": {
    "current_step": "retrieval",
    "steps_completed": 2,
    "total_steps": 4
  }
}
```

#### GET `/agent/health`

Health check endpoint.

### Metrics Endpoints

#### GET `/metrics`

Prometheus metrics endpoint.

Returns metrics in Prometheus format for monitoring.

## Running the API

```bash
# Development
uvicorn agentic_clinical_assistant.api.main:app --reload

# Production
uvicorn agentic_clinical_assistant.api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Middleware

- **CORS**: Configured from `ALLOWED_ORIGINS` setting
- **Logging**: Request/response logging with structlog
- **Error Handling**: Global exception handler

## Next Steps

- Add authentication middleware
- Implement rate limiting
- Add request validation
- Integrate with workflow engine

