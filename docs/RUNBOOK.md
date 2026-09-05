# Incident Response Runbooks & Query Cheat Sheet

This runbook guides on-call engineers through triaging and resolving alerts triggered by Alertmanager.

---

## 🚨 Incident Triage Playbooks

### 1. `HostHighCpuLoad` (Severity: CRITICAL)
- **Symptom**: Host CPU utilization exceeds 80% for > 5 minutes.
- **Immediate Actions**:
  1. Inspect container CPU breakdown on **Dashboard 1 (Infrastructure Overview)**.
  2. SSH to host and run `htop` or `top -b -n 1 | head -n 20` to identify offending processes.
  3. If a Docker container is runaway, inspect its logs: `docker logs --tail=100 vps-fastapi-app`.
  4. If traffic surge is causing CPU saturation, check **Dashboard 2 (API Performance)** for incoming RPS.

### 2. `ApiHigh5xxErrorRate` (Severity: CRITICAL)
- **Symptom**: HTTP 5xx responses exceed 5% of total traffic.
- **Immediate Actions**:
  1. Open **Dashboard 5 (Unified Logs & Traces)**.
  2. Filter Loki logs by: `{app="fastapi-app"} |= "level=ERROR"`.
  3. Look for uncaught exceptions, DB connection timeouts, or third-party service failures.
  4. Copy `trace_id` from the error log and search in Tempo to view the exact failing span waterfall.

### 3. `HighLoginFailureRate` / `ApiAbuseBurstDetected` (Severity: CRITICAL)
- **Symptom**: More than 20 login failures/min or sudden surge in 404 vulnerability scans.
- **Immediate Actions**:
  1. Open **Dashboard 4 (Security & Fail2ban)**.
  2. Identify the attacking IP addresses under the *Failed Login Timeline* or *Suspicious Probes* panels.
  3. Check Fail2ban jail status: `fail2ban-client status fastapi-auth`.
  4. Manually ban an active attacker if necessary: `sudo fail2ban-client set fastapi-auth banip <ATTACKER_IP>`.

### 4. `SuddenTrafficDrop` (Severity: CRITICAL)
- **Symptom**: API traffic drops by > 50% compared to 1 hour prior.
- **Immediate Actions**:
  1. Check **Blackbox Uptime Probe** on Dashboard 1. If probe is DOWN, DNS or Edge Nginx is down.
  2. Test API reachability: `curl -I https://api.yourdomain.com/health/live`.
  3. Inspect Nginx status: `docker logs --tail=50 vps-nginx-proxy`.

---

## 🔍 SRE Query Cheat Sheet

### Useful PromQL Queries
```promql
# Current total RPS
sum(rate(http_requests_total[1m]))

# 5xx Error percentage
(sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100)

# p95 latency per endpoint
histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m])))

# Free memory in GB
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024

# Active users count
sum(business_active_users_gauge)
```

### Useful LogQL Queries (Loki)
```logql
# All error logs from FastAPI app
{app="fastapi-app"} |= "ERROR"

# Filter logs by specific TraceID
{app="fastapi-app"} |= "3b29c8e1a4"

# Rate of failed logins
rate({app="fastapi-app"} |= "Failed login attempt" [5m])

# Nginx 429 rate-limited access logs
{app="nginx"} |= "status:429"
```
