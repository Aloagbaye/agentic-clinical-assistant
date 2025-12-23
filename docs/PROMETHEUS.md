# Prometheus Tutorial

Complete guide to setting up and using Prometheus for monitoring the agentic clinical assistant system.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running Prometheus](#running-prometheus)
5. [Querying Metrics](#querying-metrics)
6. [Alerting Rules](#alerting-rules)
7. [Troubleshooting](#troubleshooting)

## Introduction

Prometheus is a monitoring and alerting toolkit that collects metrics from the agentic clinical assistant system. It scrapes metrics from the `/metrics` endpoint and stores them in a time-series database.

### Key Concepts

- **Metrics**: Time-series data points (counters, gauges, histograms)
- **Scraping**: Prometheus periodically fetches metrics from targets
- **Labels**: Key-value pairs that add dimensions to metrics
- **Queries**: PromQL language for querying metrics

## Installation

### Option 1: Download Binary

1. **Download Prometheus**:
   ```bash
   # Windows
   # Download from https://prometheus.io/download/
   # Extract to C:\prometheus
   
   # Linux/Mac
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
   cd prometheus-2.45.0
   ```

2. **Verify Installation**:
   ```bash
   ./prometheus --version
   ```

### Option 2: Docker

```bash
docker pull prom/prometheus
```

### Option 3: Package Manager

**Windows (Chocolatey)**:
```powershell
choco install prometheus
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install prometheus
```

**Mac (Homebrew)**:
```bash
brew install prometheus
```

## Configuration

### 1. Create Prometheus Configuration File

Create `prometheus.yml` in your project root:

```yaml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate alerting rules
  external_labels:
    cluster: 'agentic-clinical-assistant'
    environment: 'development'

# Alertmanager configuration (optional)
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

# Load alerting rules
rule_files:
  - 'alerts.yml'  # Optional: alerting rules

# Scrape configurations
scrape_configs:
  # Scrape the agentic clinical assistant API
  - job_name: 'agentic-clinical-assistant'
    static_configs:
      - targets: ['localhost:8000']  # API endpoint
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
    
  # Scrape Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### 2. Create Alerting Rules (Optional)

Create `alerts.yml`:

```yaml
groups:
  - name: agentic_clinical_assistant
    interval: 30s
    rules:
      # Alert on high error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(agent_runs_total{status="failed"}[5m])) 
          / 
          sum(rate(agent_runs_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
      
      # Alert on high latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step)
          ) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected in {{ $labels.step }}"
          description: "P95 latency is {{ $value }}ms (threshold: 1000ms)"
      
      # Alert on grounding failures
      - alert: GroundingFailures
        expr: |
          sum(rate(grounding_fail_total[5m])) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High grounding failure rate"
          description: "{{ $value }} grounding failures per second"
      
      # Alert on PHI detection
      - alert: PHIDetection
        expr: |
          sum(rate(phi_redaction_events_total[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High PHI redaction rate"
          description: "{{ $value }} PHI redactions per second"
      
      # Alert on citationless answers
      - alert: CitationlessAnswers
        expr: |
          sum(rate(citationless_answer_total[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High citationless answer rate"
          description: "{{ $value }} citationless answers per second"
```

## Running Prometheus

### Option 1: Command Line

```bash
# Windows
prometheus.exe --config.file=prometheus.yml --storage.tsdb.path=./data

# Linux/Mac
./prometheus --config.file=prometheus.yml --storage.tsdb.path=./data
```

### Option 2: Docker

```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus-data:/prometheus \
  prom/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus
```

### Option 3: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    restart: unless-stopped

volumes:
  prometheus-data:
```

Then run:
```bash
docker-compose up -d prometheus
```

### Verify Prometheus is Running

1. **Check Status**:
   ```bash
   curl http://localhost:9090/-/healthy
   ```

2. **Open Web UI**:
   Navigate to http://localhost:9090

3. **Check Targets**:
   Go to Status → Targets
   - Should show `agentic-clinical-assistant` as UP

## Querying Metrics

### Prometheus Web UI

1. **Open Query Interface**:
   - Navigate to http://localhost:9090
   - Click "Graph" tab

2. **Basic Queries**:
   ```promql
   # Total agent runs
   sum(agent_runs_total)
   
   # Agent runs by status
   sum by (status) (agent_runs_total)
   
   # Current error rate
   sum(rate(agent_runs_total{status="failed"}[5m])) 
   / 
   sum(rate(agent_runs_total[5m]))
   ```

### Common Queries

#### Agent Performance

```promql
# Total runs per second
sum(rate(agent_runs_total[5m]))

# Runs by status
sum by (status) (rate(agent_runs_total[5m]))

# Step latency percentiles
histogram_quantile(0.50, sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step))
histogram_quantile(0.95, sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step))
histogram_quantile(0.99, sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step))
```

#### Safety & Quality

```promql
# Grounding failures by reason
sum by (reason) (rate(grounding_fail_total[5m]))

# Answer abstentions
sum by (reason) (rate(answers_abstained_total[5m]))

# Citationless answers rate
rate(citationless_answer_total[5m])

# PHI redactions by type
sum by (type) (rate(phi_redaction_events_total[5m]))
```

#### Backend Comparison

```promql
# MRR by backend
retrieval_mrr

# nDCG by backend
retrieval_ndcg

# Retrieval latency
histogram_quantile(0.95, sum(rate(retrieval_latency_ms_bucket[5m])) by (le, backend))

# Backend selection counts
sum by (backend, query_type) (rate(backend_selected_total[5m]))
```

#### Tool Performance

```promql
# Tool calls by tool
sum by (tool_name) (rate(tool_calls_total[5m]))

# Tool latency
histogram_quantile(0.95, sum(rate(tool_call_latency_ms_bucket[5m])) by (le, tool_name))
```

### Query API

You can also query via HTTP API:

```bash
# Query metric
curl 'http://localhost:9090/api/v1/query?query=agent_runs_total'

# Query range (for graphs)
curl 'http://localhost:9090/api/v1/query_range?query=agent_runs_total&start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&step=15s'
```

## Alerting Rules

### Setting Up Alertmanager

1. **Download Alertmanager**:
   ```bash
   wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
   tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
   ```

2. **Create Alertmanager Config** (`alertmanager.yml`):
   ```yaml
   global:
     resolve_timeout: 5m
   
   route:
     group_by: ['alertname']
     group_wait: 10s
     group_interval: 10s
     repeat_interval: 12h
     receiver: 'default'
   
   receivers:
     - name: 'default'
       email_configs:
         - to: 'admin@example.com'
           from: 'prometheus@example.com'
           smarthost: 'smtp.example.com:587'
           auth_username: 'prometheus'
           auth_password: 'password'
   ```

3. **Run Alertmanager**:
   ```bash
   ./alertmanager --config.file=alertmanager.yml
   ```

### Testing Alerts

1. **View Active Alerts**:
   - Navigate to http://localhost:9090/alerts
   - Or http://localhost:9093 (Alertmanager UI)

2. **Trigger Test Alert**:
   ```promql
   # Force high error rate (for testing)
   # Stop the API temporarily to trigger alerts
   ```

## Troubleshooting

### Metrics Not Appearing

1. **Check API Endpoint**:
   ```bash
   curl http://localhost:8000/metrics
   ```
   Should return Prometheus-formatted metrics

2. **Check Prometheus Targets**:
   - Go to Status → Targets
   - Ensure target is UP
   - Check for scrape errors

3. **Check Configuration**:
   ```bash
   # Validate config
   promtool check config prometheus.yml
   ```

### High Memory Usage

1. **Reduce Retention**:
   ```yaml
   # In prometheus.yml
   global:
     storage.tsdb.retention.time: 15d  # Keep 15 days of data
   ```

2. **Limit Series**:
   ```yaml
   global:
     storage.tsdb.max-block-duration: 2h
   ```

### Slow Queries

1. **Use Recording Rules**:
   ```yaml
   # In prometheus.yml
   rule_files:
     - 'recording_rules.yml'
   ```

   Create `recording_rules.yml`:
   ```yaml
   groups:
     - name: agentic_clinical_assistant_rules
       interval: 30s
       rules:
         - record: agent_runs:rate5m
           expr: rate(agent_runs_total[5m])
   ```

2. **Optimize Queries**:
   - Use `rate()` instead of `increase()`
   - Limit time ranges
   - Use recording rules for complex queries

### Common Issues

**Issue**: "No data points"
- **Solution**: Check scrape interval, ensure metrics are being generated

**Issue**: "Target is DOWN"
- **Solution**: Verify API is running, check network connectivity

**Issue**: "High cardinality"
- **Solution**: Review label usage, remove high-cardinality labels

## Best Practices

1. **Label Cardinality**: Keep label cardinality low (< 1000 unique combinations)
2. **Scrape Interval**: Use 15s for most metrics, 60s for slow-changing metrics
3. **Retention**: Set appropriate retention based on storage capacity
4. **Recording Rules**: Pre-compute expensive queries
5. **Alerting**: Set meaningful thresholds, avoid alert fatigue

## Next Steps

- Set up Grafana for visualization (see `GRAFANA.md`)
- Configure Alertmanager for notifications
- Set up service discovery for dynamic targets
- Implement recording rules for common queries

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Best Practices](https://prometheus.io/docs/practices/)

