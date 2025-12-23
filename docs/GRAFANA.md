# Grafana Tutorial

Complete guide to setting up and using Grafana for visualizing metrics from the agentic clinical assistant system.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Importing Dashboards](#importing-dashboards)
5. [Creating Custom Dashboards](#creating-custom-dashboards)
6. [Alerting](#alerting)
7. [Troubleshooting](#troubleshooting)

## Introduction

Grafana is an open-source analytics and visualization platform that connects to Prometheus to create beautiful dashboards for monitoring the agentic clinical assistant system.

### Key Features

- **Dashboards**: Visualize metrics with graphs, tables, and stat panels
- **Alerting**: Set up alerts based on metric thresholds
- **Annotations**: Mark events on graphs
- **Variables**: Create dynamic, reusable dashboards

## Installation

### Option 1: Download Binary

1. **Download Grafana**:
   ```bash
   # Windows
   # Download from https://grafana.com/grafana/download
   # Extract to C:\grafana
   
   # Linux/Mac
   wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz
   tar -zxvf grafana-10.0.0.linux-amd64.tar.gz
   cd grafana-10.0.0
   ```

2. **Verify Installation**:
   ```bash
   ./bin/grafana-server --version
   ```

### Option 2: Docker

```bash
docker pull grafana/grafana
```

### Option 3: Package Manager

**Windows (Chocolatey)**:
```powershell
choco install grafana
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install grafana
```

**Mac (Homebrew)**:
```bash
brew install grafana
```

## Configuration

### 1. Basic Configuration

Edit `conf/grafana.ini` (or create custom config):

```ini
[server]
http_port = 3000
domain = localhost

[database]
type = sqlite3
path = grafana.db

[security]
admin_user = admin
admin_password = admin  # Change this!

[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
```

### 2. Running Grafana

#### Option 1: Command Line

```bash
# Windows
grafana-server.exe --config=conf/grafana.ini

# Linux/Mac
./bin/grafana-server --config=conf/grafana.ini
```

#### Option 2: Docker

```bash
docker run -d \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana
```

#### Option 3: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  grafana-data:
```

Then run:
```bash
docker-compose up -d grafana
```

### 3. Access Grafana

1. **Open Web UI**:
   Navigate to http://localhost:3000

2. **Login**:
   - Username: `admin`
   - Password: `admin` (change on first login)

## Configuration

### 1. Add Prometheus Data Source

1. **Navigate to Data Sources**:
   - Click Configuration (gear icon) → Data Sources
   - Click "Add data source"
   - Select "Prometheus"

2. **Configure Connection**:
   ```
   Name: Prometheus
   URL: http://prometheus:9090  # Or http://localhost:9090 if not using Docker
   Access: Server (default)
   ```

3. **Test Connection**:
   - Click "Save & Test"
   - Should show "Data source is working"

### 2. Provision Data Source (Optional)

Create `grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

## Importing Dashboards

### Method 1: Import from JSON Files

1. **Navigate to Dashboards**:
   - Click Dashboards (four squares icon) → Import

2. **Import Dashboard**:
   - Click "Upload JSON file"
   - Select dashboard JSON file from `grafana/dashboards/`
   - Or paste JSON content

3. **Configure**:
   - Select Prometheus data source
   - Click "Import"

### Method 2: Import by ID

1. **Import Dashboard**:
   - Click "Import"
   - Enter dashboard ID (if using Grafana.com dashboards)
   - Click "Load"

### Method 3: Provision Dashboards

Create `grafana/provisioning/dashboards/dashboards.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Agentic Clinical Assistant'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: true
```

Place dashboard JSON files in `grafana/provisioning/dashboards/`

### Available Dashboards

1. **Agent Performance** (`agent-performance.json`):
   - Agent runs by status
   - Step latency percentiles
   - Tool call distribution
   - Tool call latency

2. **Safety & Quality** (`safety-quality.json`):
   - Grounding failures by reason
   - Answer abstention rates
   - Citation coverage
   - PHI redaction events

3. **Backend Comparison** (`backend-comparison.json`):
   - MRR by backend
   - nDCG by backend
   - Retrieval latency comparison
   - Backend selection patterns

4. **SLA Health** (`sla-health.json`):
   - P95 latency per agent step
   - Workflow duration by status
   - Error rates
   - Active workflows

## Creating Custom Dashboards

### 1. Create New Dashboard

1. **Create Dashboard**:
   - Click Dashboards → New → New Dashboard
   - Click "Add visualization"

2. **Select Data Source**:
   - Choose "Prometheus"

3. **Write Query**:
   ```promql
   sum(rate(agent_runs_total[5m]))
   ```

4. **Customize Panel**:
   - Change visualization type (Graph, Stat, Table, etc.)
   - Add labels, legends, thresholds
   - Set time range

### 2. Panel Types

#### Time Series (Graph)

```promql
# Agent runs over time
sum(rate(agent_runs_total[5m])) by (status)
```

**Settings**:
- Visualization: Time series
- Legend: Show as table
- Thresholds: Add warning/critical lines

#### Stat Panel

```promql
# Total agent runs
sum(agent_runs_total)
```

**Settings**:
- Visualization: Stat
- Value options: Show current value
- Thresholds: Green < 1000, Yellow < 5000, Red >= 5000

#### Gauge

```promql
# Error rate
sum(rate(agent_runs_total{status="failed"}[5m])) 
/ 
sum(rate(agent_runs_total[5m]))
```

**Settings**:
- Visualization: Gauge
- Min: 0, Max: 1
- Thresholds: Green < 0.01, Yellow < 0.05, Red >= 0.05

#### Table

```promql
# Tool calls by tool
sum by (tool_name) (rate(tool_calls_total[5m]))
```

**Settings**:
- Visualization: Table
- Transform: Organize fields
- Sort by: Value (descending)

#### Pie Chart

```promql
# Agent runs by status
sum by (status) (agent_runs_total)
```

**Settings**:
- Visualization: Pie chart
- Legend: Show legend

### 3. Dashboard Variables

Create reusable variables:

1. **Add Variable**:
   - Dashboard Settings → Variables → New variable

2. **Query Variable**:
   ```yaml
   Name: backend
   Type: Query
   Data source: Prometheus
   Query: label_values(retrieval_mrr, backend)
   ```

3. **Use in Queries**:
   ```promql
   retrieval_mrr{backend="$backend"}
   ```

### 4. Dashboard Best Practices

1. **Organization**:
   - Group related panels in rows
   - Use row titles for sections
   - Organize by importance (top to bottom)

2. **Time Ranges**:
   - Set appropriate default time range
   - Use relative times (Last 1 hour, Last 24 hours)

3. **Refresh Intervals**:
   - Set auto-refresh (30s, 1m, 5m)
   - Match Prometheus scrape interval

4. **Annotations**:
   - Add deployment markers
   - Mark incidents
   - Link to runbooks

## Alerting

### 1. Create Alert Rule

1. **Create Alert**:
   - Panel → Edit → Alert tab
   - Click "Create Alert"

2. **Configure Condition**:
   ```promql
   # Alert when error rate > 5%
   sum(rate(agent_runs_total{status="failed"}[5m])) 
   / 
   sum(rate(agent_runs_total[5m])) > 0.05
   ```

3. **Set Thresholds**:
   - Warning: 0.01 (1%)
   - Critical: 0.05 (5%)

4. **Configure Notifications**:
   - Add notification channel
   - Set evaluation interval

### 2. Notification Channels

1. **Add Channel**:
   - Alerting → Notification channels → New channel

2. **Email Channel**:
   ```yaml
   Name: Email
   Type: Email
   Addresses: admin@example.com
   ```

3. **Slack Channel**:
   ```yaml
   Name: Slack
   Type: Slack
   Webhook URL: https://hooks.slack.com/services/...
   ```

4. **Webhook Channel**:
   ```yaml
   Name: Webhook
   Type: Webhook
   URL: https://your-webhook-url.com
   ```

### 3. Alert Rules (Grafana 8.0+)

Create alert rules in Alerting section:

1. **Create Rule**:
   - Alerting → Alert rules → New alert rule

2. **Configure**:
   ```yaml
   Name: High Error Rate
   Query: sum(rate(agent_runs_total{status="failed"}[5m])) / sum(rate(agent_runs_total[5m]))
   Condition: IS ABOVE 0.05
   Evaluation: Every 1m, For 5m
   ```

## Troubleshooting

### Dashboard Not Loading

1. **Check Data Source**:
   - Verify Prometheus connection
   - Test query in Explore

2. **Check Queries**:
   - Validate PromQL syntax
   - Test queries in Prometheus UI

3. **Check Time Range**:
   - Ensure data exists for selected time range
   - Adjust time range if needed

### No Data Points

1. **Verify Metrics**:
   ```bash
   curl http://localhost:8000/metrics | grep agent_runs_total
   ```

2. **Check Time Range**:
   - Metrics might not exist for selected range
   - Use "Last 5 minutes" to test

3. **Check Query**:
   - Test query in Prometheus UI first
   - Verify metric names match exactly

### Performance Issues

1. **Optimize Queries**:
   - Use recording rules for complex queries
   - Limit time ranges
   - Reduce panel count

2. **Reduce Refresh Rate**:
   - Increase refresh interval
   - Disable auto-refresh for heavy dashboards

### Common Issues

**Issue**: "Data source not found"
- **Solution**: Re-add data source, check URL

**Issue**: "Query timeout"
- **Solution**: Simplify query, use recording rules

**Issue**: "No data"
- **Solution**: Check time range, verify metrics exist

## Best Practices

1. **Dashboard Design**:
   - Keep dashboards focused (one per use case)
   - Use consistent color schemes
   - Add descriptions and documentation

2. **Query Optimization**:
   - Use recording rules for expensive queries
   - Limit time ranges appropriately
   - Use rate() instead of increase()

3. **Alerting**:
   - Set meaningful thresholds
   - Avoid alert fatigue
   - Use alert grouping

4. **Organization**:
   - Use folders for dashboard organization
   - Tag dashboards appropriately
   - Set appropriate permissions

## Example Dashboard Queries

### Agent Performance Dashboard

```promql
# Total runs per second
sum(rate(agent_runs_total[5m]))

# Runs by status
sum by (status) (rate(agent_runs_total[5m]))

# P95 latency by step
histogram_quantile(0.95, sum(rate(agent_step_latency_ms_bucket[5m])) by (le, step))
```

### Safety Dashboard

```promql
# Grounding failures
sum by (reason) (rate(grounding_fail_total[5m]))

# PHI redactions
sum by (type) (rate(phi_redaction_events_total[5m]))

# Citationless answers
rate(citationless_answer_total[5m])
```

### Backend Performance Dashboard

```promql
# MRR comparison
retrieval_mrr

# Latency comparison
histogram_quantile(0.95, sum(rate(retrieval_latency_ms_bucket[5m])) by (le, backend))

# Selection counts
sum by (backend) (rate(backend_selected_total[5m]))
```

## Next Steps

- Set up alerting rules for critical metrics
- Create custom dashboards for your use cases
- Configure notification channels
- Set up dashboard provisioning
- Explore Grafana plugins and integrations

## Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Data Source](https://grafana.com/docs/grafana/latest/datasources/prometheus/)
- [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [Alerting Guide](https://grafana.com/docs/grafana/latest/alerting/)

