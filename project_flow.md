You are a Principal Site Reliability Engineer (SRE), DevOps Architect, and Observability Engineer.

Design a complete end-to-end observability platform that monitors BOTH:

1. Infrastructure (VPS / servers / containers)
2. Application layer (APIs / FastAPI / microservices)
3. Business metrics (usage, requests, users, latency patterns)

This system must be production-grade and comparable to Datadog + AWS CloudWatch + New Relic combined.

---

# 🎯 CORE OBJECTIVE

Build a system that monitors:

## 🖥 Infrastructure Layer
- CPU usage per VPS
- RAM usage
- Disk I/O and storage usage
- Network traffic (in/out)
- Load average
- Process-level monitoring
- Container health (Docker)

## 🚀 Application Layer (VERY IMPORTANT)
For FastAPI / backend services:

- Request rate (RPS)
- Endpoint latency (p50, p95, p99)
- Error rate (4xx / 5xx)
- Request per route (/login, /register, /api/*)
- Response time per endpoint
- Active users (concurrent sessions)
- API uptime / health checks
- Database query latency (PostgreSQL/MySQL if used)
- External API latency (third-party calls)

## 📊 Business Metrics Layer (CRITICAL)
Track real system usage:

- Total active users per hour/day
- New user registrations
- Login success vs failure rate
- API usage per client / token
- Feature usage tracking (endpoint-based analytics)
- Revenue-related events (if applicable)
- Rate limiting hits
- Abuse / suspicious traffic detection

---

# 🧱 REQUIRED STACK

You MUST include:

## Metrics
- Prometheus (core metrics engine)
- Node Exporter (VPS metrics)
- cAdvisor (container metrics)
- Blackbox Exporter (uptime checks)

## Application Metrics (IMPORTANT ADDITION)
- Prometheus client instrumentation for FastAPI
- OpenTelemetry SDK (for traces + metrics)
- Custom business metrics exporter

## Logs
- Loki (log aggregation)
- Promtail (log shipping)

## Tracing
- OpenTelemetry Collector
- Tempo or Jaeger (distributed tracing)

## Visualization
- Grafana dashboards (full system visibility)

## Alerting
- Alertmanager
- Telegram + Email alerts

---

# 🧠 ARCHITECTURE REQUIREMENT

Provide full architecture showing:

VPS Nodes
→ Node Exporter / cAdvisor / App metrics
→ Prometheus (central or federated)
→ Loki (logs pipeline)
→ OpenTelemetry (traces pipeline)
→ Grafana (visualization)
→ Alertmanager (notifications)

---

# 📦 DEPLOYMENT OUTPUT (MANDATORY)

Generate:

- docker-compose.yml (full stack)
- prometheus.yml (multi-service scraping)
- alertmanager.yml (Telegram alerts)
- loki.yml
- promtail config
- otel-collector config

---

# 🌐 FASTAPI INTEGRATION (VERY IMPORTANT)

Provide production FastAPI instrumentation:

- /metrics endpoint (Prometheus format)
- OpenTelemetry middleware
- request latency tracking
- route-level metrics
- error tracking middleware
- request ID / trace ID propagation
- DB query timing instrumentation

---

# 📊 GRAFANA DASHBOARDS (REQUIRED)

Create dashboards for:

## Infrastructure Dashboard
- CPU / RAM / Disk / Network per VPS

## API Performance Dashboard
- Requests per second (RPS)
- Latency heatmap (p50/p95/p99)
- Error rate trends
- Top slow endpoints

## Business Dashboard
- Active users
- Requests per user
- Login success rate
- Feature usage analytics

## Logs Dashboard
- Error logs timeline
- API exceptions grouped

## Tracing Dashboard
- request flow visualization
- service dependency graph

---

# 🚨 ALERTING SYSTEM (ADVANCED)

Alert rules:

## Infrastructure
- CPU > 80%
- RAM > 85%
- Disk > 90%

## API Health
- error rate > 5%
- latency p95 > threshold
- service down

## Business Anomalies
- sudden traffic drop (>50%)
- spike in failed logins
- abnormal API usage pattern
- suspicious request bursts

Notifications:
- Telegram bot (required)
- Email fallback
- optional Discord webhook

---

# 🔐 SECURITY REQUIREMENTS

Include:

- firewall rules (UFW/iptables)
- secure Prometheus exposure (no public access)
- Grafana authentication
- TLS (Let’s Encrypt via Nginx/Traefik)
- optional VPN-only metrics access
- API auth instrumentation safety

---

# 📈 SCALABILITY DESIGN

Must include:

- multi-VPS scaling strategy
- Prometheus federation OR Thanos
- horizontal scaling for collectors
- log retention strategy (Loki)
- high availability Grafana
- storage optimization strategy

---

# 🧠 ADVANCED FEATURES (IMPORTANT)

Include:

- anomaly detection (baseline traffic modeling)
- auto alert noise reduction
- predictive CPU/RAM spikes
- auto-healing suggestions (restart services)
- rate-limiting detection layer
- observability cost optimization strategy

---

# 📤 OUTPUT FORMAT

Return in:

1. System Overview
2. Full Architecture Diagram
3. Metrics Model (infra + app + business)
4. Folder Structure
5. docker-compose.yml
6. Config Files (Prometheus, Loki, OTel, Alertmanager)
7. FastAPI Instrumentation Code
8. Grafana Dashboards (JSON or IDs)
9. Alert Rules (detailed)
10. Security Hardening Guide
11. Scaling Strategy (1 → 100 VPS)
12. Future Enhancements (AI observability)

---

# ⚠️ QUALITY BAR

- Must be production-ready (not tutorial)
- Must include real-world failure scenarios
- Must assume high traffic SaaS environment
- Must include cost-aware design decisions
- Must support real API workloads
