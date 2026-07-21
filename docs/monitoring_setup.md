# Prometheus & Grafana Monitoring Architecture

This document outlines the telemetry pipeline and Grafana dashboard layout for tracking application health, API request metrics, LangGraph execution times, and vector database query performance.

---

## 1. Monitoring Flow

```
[ Django Backend ] ────► /metrics ───┐
[ FastAPI AI ] ────────► /metrics ───┼──► [ Prometheus Scraper ] ──► [ Grafana UI ]
[ FastAPI ML ] ────────► /metrics ───┘
```

1. **Instrumentation**:
   - The Django backend is instrumented with `django-prometheus`. It exposes CPU usage, cache stats, database metrics, and HTTP request statistics on `/metrics`.
   - FastAPI services (`ai-service` and `ml-service`) are instrumented using `prometheus-fastapi-instrumentator`, exposing request histograms at `/metrics`.
2. **Collection**:
   - Prometheus scrapes metrics from each service container every 5 seconds.
3. **Visualization**:
   - Grafana pulls data from Prometheus and renders real-time metric panels.

---

## 2. Grafana Dashboard Panels & PromQL

We provisioned a unified dashboard at [nexus-dashboard.json](file:///c:/Users/tanis/OneDrive/Desktop/nexus/docker/grafana/dashboards/nexus-dashboard.json).

### 2.1 HTTP Request Latency (p95)
Measures the 95th percentile duration of HTTP requests across endpoints.
- **Metric**: `http_request_duration_seconds_bucket`
- **PromQL**:
  ```promql
  histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path))
  ```

### 2.2 HTTP 5xx Error Rate
Tracks the rate of server crash responses (HTTP status codes 500-599).
- **Metric**: `http_requests_total`
- **PromQL**:
  ```promql
  sum(rate(http_requests_total{status=~"5.."}[5m]))
  ```

### 2.3 Agent Step Execution Time (LangGraph)
Measures the latency of LangGraph agent steps in the AI core.
- **Metric**: `ai_agent_execution_duration_seconds_bucket`
- **PromQL**:
  ```promql
  histogram_quantile(0.95, sum(rate(ai_agent_execution_duration_seconds_bucket[5m])) by (le))
  ```

### 2.4 RAG Retrieval Latency (Vector Search)
Tracks pgvector query latency. High latency indicates index rebuilding, search space bloating, or memory exhaustion.
- **Metric**: `ai_vector_search_duration_seconds_bucket`
- **PromQL**:
  ```promql
  histogram_quantile(0.95, sum(rate(ai_vector_search_duration_seconds_bucket[5m])) by (le))
  ```

---

## 3. Alerting Thresholds

We define standard alerting rules to trigger notifications (Slack/PagerDuty/Email) when core metrics cross critical thresholds:

### 3.1 Severity: Warning (High Latency / Degraded)
- **HTTP Latency**: p95 HTTP request duration $> 1.0\text{s}$ for 5 consecutive minutes.
  - *Mitigation*: Inspect database locks, check Redis connection exhaustion, or inspect CPU throttles.
- **RAG Latency**: p95 vector retrieval latency $> 500\text{ms}$ for 5 minutes.
  - *Mitigation*: Re-index HNSW vector spaces or check connection limits on RDS pgvector.

### 3.2 Severity: Critical (Service Outage / System Down)
- **HTTP Error Rate**: $5\text{xx}$ error rate $> 5\%$ of total requests within a 2-minute window.
  - *Mitigation*: Roll back the latest release, verify DB/API connection variables, check storage exhaustion.
- **Agent Failures**: LangGraph executor node errors $> 10\%$ in 5 minutes.
  - *Mitigation*: Verify OpenAI/Anthropic model endpoints, check API credentials, or reset token rate-limits.
