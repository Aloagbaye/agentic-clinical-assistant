# Metrics & Observability

Comprehensive metrics collection for monitoring and observability of the agentic clinical assistant system.

## Overview

The metrics system uses Prometheus for metric collection and provides Grafana dashboards for visualization.

## Metrics

### Agent Run Metrics

- **`agent_runs_total{status}`**: Total number of agent runs by status (success, failed, cancelled)
- **`agent_step_latency_ms{step}`**: Latency for each agent step (intake, retrieve, synthesize, verify)
- **`workflow_duration_ms{status}`**: Complete workflow duration by status
- **`active_workflows`**: Number of currently active workflows

### Tool Call Metrics

- **`tool_calls_total{tool_name,backend}`**: Total number of tool calls by tool and backend
- **`tool_call_latency_ms{tool_name}`**: Tool call latency by tool name

### Safety & Grounding Metrics

- **`grounding_fail_total{reason}`**: Grounding failures by reason (no_citations, weak_grounding, citation_mismatch)
- **`answers_abstained_total{reason}`**: Answer abstentions by reason (phi_detected, grounding_fail, unsafe_content)
- **`citationless_answer_total`**: Total number of answers without citations
- **`phi_redaction_events_total{type}`**: PHI redaction events by type (ssn, phone, email, date, name, address)

### Backend Comparison Metrics

- **`retrieval_mrr{backend}`**: Mean Reciprocal Rank by backend
- **`retrieval_ndcg{backend}`**: Normalized Discounted Cumulative Gain by backend
- **`retrieval_recall_at_k{backend,k}`**: Recall@K by backend and K value
- **`retrieval_latency_ms{backend}`**: Retrieval latency by backend
- **`backend_selected_total{backend,query_type}`**: Backend selection counts by backend and query type

### Memory Metrics

- **`session_memory_total`**: Total number of active sessions
- **`policy_memory_access_total{doc_hash}`**: Policy memory access counts by document hash

## Usage

### Recording Metrics

```python
from agentic_clinical_assistant.metrics.collector import MetricsCollector

# Record agent run
MetricsCollector.record_agent_run("success")

# Record step latency
MetricsCollector.record_agent_step_latency("intake", 150.5)

# Record tool call
MetricsCollector.record_tool_call("retrieve_evidence", "faiss", 200.0)

# Record grounding failure
MetricsCollector.record_grounding_fail("weak_grounding")

# Record PHI redaction
MetricsCollector.record_phi_redaction("ssn")

# Record retrieval metrics
MetricsCollector.record_retrieval_metrics(
    backend="faiss",
    mrr=0.85,
    ndcg=0.90,
    recall_at_k={1: 0.80, 5: 0.95, 10: 0.98},
    latency_ms=150.0
)
```

## API Endpoint

### GET /metrics

Returns Prometheus-formatted metrics:

```bash
curl http://localhost:8000/metrics
```

## Grafana Dashboards

### 1. Agent Performance

- Agent runs by status
- Step latency (p50, p95, p99)
- Tool call distribution
- Tool call latency

**Location**: `grafana/dashboards/agent-performance.json`

### 2. Safety & Quality

- Grounding failures by reason
- Answer abstention rates
- Citation coverage
- PHI redaction events

**Location**: `grafana/dashboards/safety-quality.json`

### 3. Backend Comparison

- MRR by backend
- nDCG by backend
- Retrieval latency comparison
- Backend selection patterns

**Location**: `grafana/dashboards/backend-comparison.json`

### 4. SLA Health

- P95 latency per agent step
- Workflow duration by status
- Error rates
- Active workflows

**Location**: `grafana/dashboards/sla-health.json`

## Integration

Metrics are automatically collected throughout the system:

- **Workflow Engine**: Records workflow duration, step latencies, and run status
- **Agents**: Records step latencies and agent-specific metrics
- **Tools**: Records tool call counts and latencies
- **Retrieval**: Records backend selection and retrieval metrics
- **Verifier**: Records grounding failures and PHI redactions

## Prometheus Configuration

Example Prometheus scrape configuration:

```yaml
scrape_configs:
  - job_name: 'agentic-clinical-assistant'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Grafana Setup

1. Import dashboard JSON files from `grafana/dashboards/`
2. Configure Prometheus data source
3. Set refresh interval (default: 30s)
4. Configure alerts (optional)

## Alerting Rules (Optional)

Example Prometheus alerting rules:

```yaml
groups:
  - name: agentic_clinical_assistant
    rules:
      - alert: HighErrorRate
        expr: sum(rate(agent_runs_total{status="failed"}[5m])) / sum(rate(agent_runs_total[5m])) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step)) > 1000
        for: 5m
        annotations:
          summary: "High latency detected in {{ $labels.step }}"
      
      - alert: GroundingFailures
        expr: sum(rate(grounding_fail_total[5m])) > 10
        for: 5m
        annotations:
          summary: "High grounding failure rate"
```

## Best Practices

1. **Metric Naming**: Use consistent naming conventions (snake_case)
2. **Labels**: Use labels for dimensions (status, backend, query_type)
3. **Cardinality**: Avoid high-cardinality labels (e.g., user_id)
4. **Buckets**: Use appropriate histogram buckets for latency metrics
5. **Rate Calculation**: Use `rate()` for counters, `increase()` for totals

## Troubleshooting

### Metrics Not Appearing

1. Check that metrics endpoint is accessible: `curl http://localhost:8000/metrics`
2. Verify Prometheus is scraping the endpoint
3. Check metric names match exactly (case-sensitive)
4. Ensure metrics are being recorded (check code integration)

### High Cardinality

If you see high cardinality warnings:

1. Review label usage
2. Remove high-cardinality labels (e.g., doc_hash)
3. Use aggregation functions in queries
4. Consider using exemplars for detailed tracing

## Next Steps

- Add distributed tracing (Tempo/Jaeger)
- Integrate structured logging (Loki)
- Add custom business metrics
- Implement metric-based alerting

