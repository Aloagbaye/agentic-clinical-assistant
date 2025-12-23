# Kubernetes Deployment Tutorial

This guide shows how to deploy the PHI-Safe Clinical Ops Copilot to Kubernetes using the manifests in `k8s/` (base + overlays). It covers local test with kind/minikube, dev deploy with Kustomize, secrets, ingress, scaling, and troubleshooting.

## Prerequisites
- kubectl v1.27+ installed and pointing to your cluster
- Kustomize (kubectl has `-k` support built in)
- Docker/OCI registry access if pushing custom images
- Optional: kind or minikube for local testing

## Layout
- `k8s/base/` — Deployments, Services, ConfigMap, Secrets example, HPA, Ingress, Kustomization
- `k8s/overlays/dev/` — Dev overrides (image tags, env tweaks)

## Quick Start (local kind)
```bash
# 1) Create a kind cluster (requires Docker)
kind create cluster --name aca

# 2) Build and load images into kind (optional if using public images)
docker build -f docker/Dockerfile.api -t agentic-clinical-assistant/api:local .
docker build -f docker/Dockerfile.worker -t agentic-clinical-assistant/worker:local .
kind load docker-image agentic-clinical-assistant/api:local --name aca
kind load docker-image agentic-clinical-assistant/worker:local --name aca

# 3) Apply base + dev overlay
kubectl apply -k k8s/overlays/dev

# 4) Check status
kubectl get pods,svc,ingress -n default
```

## Dev Deploy (generic cluster)
```bash
# Point kubectl to your dev cluster
kubectl config use-context <dev-context>

# Set image tags (optional if using latest)
IMAGE_TAG=$(git rev-parse --short HEAD)
kubectl set image deployment/agent-api agent-api=agentic-clinical-assistant/api:${IMAGE_TAG} -n dev || true
kubectl set image deployment/worker worker=agentic-clinical-assistant/worker:${IMAGE_TAG} -n dev || true

# Apply manifests
kubectl apply -k k8s/overlays/dev
```

## Configuration & Secrets
- Config: `k8s/base/configmap.yaml`
- Secrets: `k8s/base/secrets.yaml.example` (copy to a secure location or use external secret store)
- Key env vars: database URL, Redis URL, OpenAI/LLM keys, vector backends, telemetry endpoints

### Creating secrets (imperative example)
```bash
kubectl create secret generic aca-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/aca" \
  --from-literal=REDIS_URL="redis://redis:6379/0" \
  --from-literal=OPENAI_API_KEY="sk-..." \
  -n dev
```

## Ingress
- Base ingress: `k8s/base/ingress.yaml`
- Update host to your domain.
- For local kind, enable ingress controller (e.g., nginx ingress) and map host to `127.0.0.1` in `/etc/hosts`.

## Horizontal Pod Autoscaling
- HPAs: `k8s/base/hpa-api.yaml`, `k8s/base/hpa-worker.yaml`
- Uses CPU by default; extend with custom metrics if Prometheus adapter is present.

## Health Checks
- API liveness/readiness: `/health`
- Worker liveness/readiness: Celery worker pod relies on process health; consider adding custom sidecar/exec checks if needed.

## Observability
- Prometheus scrape: ensure Service annotations or ServiceMonitor (if using Prometheus Operator)
- Grafana dashboards are provided in `grafana/dashboards/`
- Logs: ship via stdout to your log stack (e.g., Loki/ELK)

## Rolling Deploy
```bash
kubectl set image deployment/agent-api \
  agent-api=agentic-clinical-assistant/api:${IMAGE_TAG} -n dev
kubectl set image deployment/worker \
  worker=agentic-clinical-assistant/worker:${IMAGE_TAG} -n dev
kubectl rollout status deployment/agent-api -n dev
kubectl rollout status deployment/worker -n dev
```

## Smoke Test
```bash
API_URL=http://<ingress-host>
curl -s ${API_URL}/health
curl -s -X POST ${API_URL}/agent/run -H "Content-Type: application/json" \
  -d '{"query":"Test agent","user_id":"demo"}'
```

## Troubleshooting
- Pods CrashLoop: `kubectl logs <pod>` and `kubectl describe pod <pod>`
- DB/Redis not reachable: verify env vars and service DNS (`db`, `redis` in compose vs cluster service names)
- Ingress 404: check ingress controller logs, host rules, and Service targets/ports
- HPA not scaling: ensure metrics-server present; check `kubectl top pods`
- Image pull errors: ensure image registry access; set imagePullSecrets if private

## Cleanup (kind)
```bash
kind delete cluster --name aca
```

## Next Steps
- Add TLS to ingress (e.g., cert-manager)
- Use External Secrets for secret management
- Add ServiceMonitor and PrometheusRule for metrics/alerts

