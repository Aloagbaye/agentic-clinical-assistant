# Phase 8 – Testing & Evaluation

This phase establishes a repeatable testing and evaluation discipline for the PHI-Safe Clinical Ops Copilot. It layers unit → integration → contract → smoke tests, plus offline/online evaluations and backend benchmarking.

## Objectives
- Validate correctness, safety, grounding, and PHI-safety of the agentic workflow.
- Provide automated, repeatable evaluations with clear quality gates.
- Benchmark vector backends and end-to-end latency/cost.

## Test / Eval Types
- **Unit**: agents, tools, memory, workflow engine, API models.
- **Integration**: API + workers + DB + vector backends via `docker-compose.test.yml`.
- **Contract**: OpenAPI schema compatibility and backward-compatibility.
- **Smoke**: health, simple agent run, PHI leakage & citation checks.
- **Offline evals**: curated de-identified prompts graded by heuristics + LLM-as-judge.
- **Online evals**: canary/shadow traffic; SLO checks (latency, error, grounding, PHI).
- **Benchmarking**: vector backend latency/recall, LLM/tool latency, cost per run.

## Metrics (examples)
- Grounding score, factuality, hallucination rate.
- PHI leakage (regex/keyword/NER-based heuristics).
- Citation coverage and correctness.
- Checklist / action-extraction precision & recall.
- Latency: per-agent, per-tool, overall p95/p99.
- Backend comparison: latency, recall@k, throughput.

## Quality Gates (suggested)
- PHI leakage = 0 findings.
- Grounding score ≥ 0.90.
- Citation coverage ≥ 0.90.
- Latency p95 ≤ target (e.g., 3s) per critical stage.
- Error rate ≤ 1%.

## Automation Plan
- **CI (fast path)**: lint, unit, contract tests.
- **Nightly (slow path)**: integration, smoke, offline eval suite, backend benchmarks; publish reports.
- **On-demand**: make/jenkins job to run a subset locally.

## File/Script Additions
- `scripts/eval/run_offline_eval.py` — run offline evals over a dataset; emit JSON summary.
- `scripts/eval/benchmark_backends.py` — optional backend latency/throughput probe; skips missing deps.
- (Existing) `tests/` suites, `docker-compose.test.yml` for integration, `scripts/ci/check_*` for PHI/citation.

## How to Run
### Offline eval (API required)
```bash
python scripts/eval/run_offline_eval.py \
  --dataset data/eval/offline_eval.jsonl \
  --base-url http://localhost:8000 \
  --out artifacts/offline_eval_report.json
```

Dataset JSONL schema (per line):
```json
{
  "id": "case-1",
  "query": "Summarize the clinical note and list next steps.",
  "expected_keywords": ["summary", "plan", "assessment"],
  "allow_phi": false
}
```

### Backend benchmark (optional, best-effort)
```bash
python scripts/eval/benchmark_backends.py --backends faiss pinecone weaviate --out artifacts/backend_bench.json
```
Backends with missing deps/config are skipped safely.

## Reporting & Dashboards
- Store JSON/HTML reports as build artifacts.
- Add Grafana panels: eval scores, PHI findings, grounding pass/fail, latency per stage, backend comparison.

## Troubleshooting
- API unreachable: start API/worker stack or point `--base-url` correctly.
- Missing deps (requests, faiss, pinecone, weaviate): install selectively; scripts skip if absent.
- No Docker/compose during integration: run via `docker-compose.test.yml` per existing docs.

