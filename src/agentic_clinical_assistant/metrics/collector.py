"""Prometheus metrics collector."""

from typing import Dict

from prometheus_client import Counter, Gauge, Histogram

# Agent Run Metrics
agent_runs_total = Counter(
    "agent_runs_total",
    "Total number of agent runs",
    ["status"],  # status: success, failed, cancelled
)

agent_step_latency_ms = Histogram(
    "agent_step_latency_ms",
    "Agent step latency in milliseconds",
    ["step"],  # step: intake, retrieve, synthesize, verify
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000, 10000],
)

# Tool Call Metrics
tool_calls_total = Counter(
    "tool_calls_total",
    "Total number of tool calls",
    ["tool_name", "backend"],  # backend: faiss, pinecone, weaviate, none
)

tool_call_latency_ms = Histogram(
    "tool_call_latency_ms",
    "Tool call latency in milliseconds",
    ["tool_name"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000],
)

# Safety & Grounding Metrics
grounding_fail_total = Counter(
    "grounding_fail_total",
    "Total number of grounding failures",
    ["reason"],  # reason: no_citations, weak_grounding, citation_mismatch
)

answers_abstained_total = Counter(
    "answers_abstained_total",
    "Total number of answers abstained",
    ["reason"],  # reason: phi_detected, grounding_fail, unsafe_content
)

citationless_answer_total = Counter(
    "citationless_answer_total",
    "Total number of answers without citations",
)

phi_redaction_events_total = Counter(
    "phi_redaction_events_total",
    "Total number of PHI redaction events",
    ["type"],  # type: ssn, phone, email, date, name, address
)

# Backend Comparison Metrics
retrieval_mrr = Gauge(
    "retrieval_mrr",
    "Mean Reciprocal Rank for retrieval",
    ["backend"],  # backend: faiss, pinecone, weaviate
)

retrieval_ndcg = Gauge(
    "retrieval_ndcg",
    "Normalized Discounted Cumulative Gain for retrieval",
    ["backend"],
)

retrieval_recall_at_k = Gauge(
    "retrieval_recall_at_k",
    "Recall@K for retrieval",
    ["backend", "k"],  # k: 1, 5, 10, 20
)

retrieval_latency_ms = Histogram(
    "retrieval_latency_ms",
    "Retrieval latency in milliseconds",
    ["backend"],
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000],
)

backend_selected_total = Counter(
    "backend_selected_total",
    "Total number of times a backend was selected",
    ["backend", "query_type"],  # query_type: policy_lookup, summarize, compare, explain
)

# Workflow Metrics
workflow_duration_ms = Histogram(
    "workflow_duration_ms",
    "Complete workflow duration in milliseconds",
    ["status"],
    buckets=[100, 500, 1000, 2000, 5000, 10000, 30000, 60000],
)

active_workflows = Gauge(
    "active_workflows",
    "Number of currently active workflows",
)

# Memory Metrics
session_memory_total = Gauge(
    "session_memory_total",
    "Total number of active sessions",
)

policy_memory_access_total = Counter(
    "policy_memory_access_total",
    "Total number of policy memory accesses",
    ["doc_hash"],
)


class MetricsCollector:
    """Metrics collector for agentic clinical assistant."""

    @staticmethod
    def record_agent_run(status: str) -> None:
        """
        Record agent run.

        Args:
            status: Run status (success, failed, cancelled)
        """
        agent_runs_total.labels(status=status).inc()

    @staticmethod
    def record_agent_step_latency(step: str, latency_ms: float) -> None:
        """
        Record agent step latency.

        Args:
            step: Step name (intake, retrieve, synthesize, verify)
            latency_ms: Latency in milliseconds
        """
        agent_step_latency_ms.labels(step=step).observe(latency_ms)

    @staticmethod
    def record_tool_call(tool_name: str, backend: str = "none", latency_ms: float = 0.0) -> None:
        """
        Record tool call.

        Args:
            tool_name: Tool name
            backend: Backend used (faiss, pinecone, weaviate, none)
            latency_ms: Latency in milliseconds
        """
        tool_calls_total.labels(tool_name=tool_name, backend=backend).inc()
        if latency_ms > 0:
            tool_call_latency_ms.labels(tool_name=tool_name).observe(latency_ms)

    @staticmethod
    def record_grounding_fail(reason: str) -> None:
        """
        Record grounding failure.

        Args:
            reason: Failure reason (no_citations, weak_grounding, citation_mismatch)
        """
        grounding_fail_total.labels(reason=reason).inc()

    @staticmethod
    def record_answer_abstained(reason: str) -> None:
        """
        Record answer abstention.

        Args:
            reason: Abstention reason (phi_detected, grounding_fail, unsafe_content)
        """
        answers_abstained_total.labels(reason=reason).inc()

    @staticmethod
    def record_citationless_answer() -> None:
        """Record answer without citations."""
        citationless_answer_total.inc()

    @staticmethod
    def record_phi_redaction(phi_type: str) -> None:
        """
        Record PHI redaction event.

        Args:
            phi_type: Type of PHI (ssn, phone, email, date, name, address)
        """
        phi_redaction_events_total.labels(type=phi_type).inc()

    @staticmethod
    def record_retrieval_metrics(
        backend: str,
        mrr: float = None,
        ndcg: float = None,
        recall_at_k: Dict[int, float] = None,
        latency_ms: float = None,
    ) -> None:
        """
        Record retrieval metrics.

        Args:
            backend: Backend name
            mrr: Mean Reciprocal Rank
            ndcg: Normalized Discounted Cumulative Gain
            recall_at_k: Dictionary of recall@k values
            latency_ms: Latency in milliseconds
        """
        if mrr is not None:
            retrieval_mrr.labels(backend=backend).set(mrr)
        if ndcg is not None:
            retrieval_ndcg.labels(backend=backend).set(ndcg)
        if recall_at_k:
            for k, recall in recall_at_k.items():
                retrieval_recall_at_k.labels(backend=backend, k=str(k)).set(recall)
        if latency_ms is not None:
            retrieval_latency_ms.labels(backend=backend).observe(latency_ms)

    @staticmethod
    def record_backend_selected(backend: str, query_type: str) -> None:
        """
        Record backend selection.

        Args:
            backend: Backend name
            query_type: Query type (policy_lookup, summarize, compare, explain)
        """
        backend_selected_total.labels(backend=backend, query_type=query_type).inc()

    @staticmethod
    def record_workflow_duration(status: str, duration_ms: float) -> None:
        """
        Record workflow duration.

        Args:
            status: Workflow status (success, failed, cancelled)
            duration_ms: Duration in milliseconds
        """
        workflow_duration_ms.labels(status=status).observe(duration_ms)

    @staticmethod
    def set_active_workflows(count: int) -> None:
        """
        Set active workflows count.

        Args:
            count: Number of active workflows
        """
        active_workflows.set(count)

    @staticmethod
    def set_session_memory_total(count: int) -> None:
        """
        Set session memory total.

        Args:
            count: Number of active sessions
        """
        session_memory_total.set(count)

    @staticmethod
    def record_policy_memory_access(doc_hash: str) -> None:
        """
        Record policy memory access.

        Args:
            doc_hash: Document hash
        """
        policy_memory_access_total.labels(doc_hash=doc_hash).inc()

