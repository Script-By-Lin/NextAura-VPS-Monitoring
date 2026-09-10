# NextAura VPS Monitoring & Nginx DevOps Platform
## Complete Usage Manual & Command Reference Guide 📖⚡

A comprehensive operational manual detailing all CLI commands, parameters, flags, interactive menu options, API endpoints, web dashboards, and teardown procedures.

---

## 📑 Table of Contents
1. [Core Platform Lifecycle Commands (`./aura`)](#1-core-platform-lifecycle-commands)
2. [Comprehensive System & Project View Commands](#2-comprehensive-system--project-view-commands)
3. [Nginx Reverse Proxy & SSL DevOps Automation (`./aura nginx`)](#3-nginx-reverse-proxy--ssl-devops-automation)
4. [Monitoring, Scanning & Proactive Security Tools](#4-monitoring-scanning--proactive-security-tools)
5. [Complete Service Deletion & Teardown Commands](#5-complete-service-deletion--teardown-commands)
6. [Interactive Master Control Center (Menu Options 0–24)](#6-interactive-master-control-center-menu-options)
7. [Web Interfaces, Access URLs & Default Credentials](#7-web-interfaces-access-urls--default-credentials)
8. [Pre-Provisioned Grafana Dashboards](#8-pre-provisioned-grafana-dashboards)
9. [FastAPI APM & Chaos Testing Endpoints](#9-fastapi-apm--chaos-testing-endpoints)
10. [Fail2ban Security Jails & Alert Rules](#10-fail2ban-security-jails--alert-rules)

---

## 1. Core Platform Lifecycle Commands

Primary commands to build, start, stop, restart, and inspect the 11 observability and security microservices.

| Command Syntax | Alternative / Alias | Description & Actions | Flags & Arguments | Example Usage |
| :--- | :--- | :--- | :--- | :--- |
| **`./aura`** | `./aura menu`, `make` | Launches the interactive Master Control Center terminal console. | None | `./aura` |
| **`./aura up`** | `./aura start`, `make up` | Builds and starts all 11 Docker containers in detached mode. | None | `./aura up` |
| **`./aura down`** | `./aura stop`, `make down` | Gracefully stops and shuts down all active monitoring containers. | None | `./aura down` |
| **`./aura restart`** | `make restart` | Restarts all containers without rebuilding images. | None | `./aura restart` |
| **`./aura status`** | `./aura ps`, `make status` | Displays container names, running states, healthcheck results, and port bindings. | None | `./aura status` |
| **`./aura logs`** | `make logs` | Streams live logs from all containers. | `[service]` (optional specific container name) | `./aura logs vps-fastapi-app` |
| **`./aura health`** | `./aura healthcheck`, `make healthcheck` | Executes end-to-end HTTP probes against all 10 services and Prometheus scrape targets. | None | `./aura health` |
| **`./aura help`** | `./aura -h`, `make help` | Displays full CLI command reference and usage guide. | None | `./aura help` |

---

## 2. Comprehensive System & Project View Commands

Commands dedicated to inspecting infrastructure, Nginx virtual hosts, service credentials, and health metrics.

| Command Syntax | Output & Scope | Detailed Information Displayed |
| :--- | :--- | :--- |
| **`./aura view`** | **All-in-One 4-Dimensional System View** | 1. **Nginx Projects Table**: Project Code (`SE-001`), Project Name, Domains, Active Route Mappings, SSL Status.<br>2. **Endpoints & Passwords**: Live URLs and credentials for Grafana, FastAPI, Prometheus, Alertmanager, Loki, Tempo, and Nginx.<br>3. **Docker Containers**: Runtime table with container status and port bindings.<br>4. **Host Hardware**: Detected OS, CPU Cores, Total RAM, Free Root Storage, and Detected Public IP. |
| **`./aura nginx list`** | **Nginx SQLite Project Registry** | Formatted table listing all configured virtual hosts, Project Codes (`SE-001`, `SE-002`), domain names, upstream proxies, SSL certificates, config file locations, and last updated timestamps. |
| **`./aura nginx status`** | **Nginx & Host Diagnostics** | Checks Nginx installation, systemd daemon status, boot enablement, active firewall (`UFW`/`Firewalld`), and network interfaces. |
| **`./aura nginx preview`** | **Dry-Run Virtual Host Preview** | Renders Jinja2 Nginx virtual host configuration syntax with TLSv1.2/1.3, security headers, and WebSockets without touching `/etc/nginx`. |

---

## 3. Nginx Reverse Proxy & SSL DevOps Automation

The embedded **Nginx-Setup** DevOps engine empowers you to deploy virtual hosts, issue Let's Encrypt certificates, generate OpenSSL IP SAN certificates, and orchestrate backend routing.

### 3.1 Nginx Subcommands Summary

| Command | Action / Purpose | Non-Interactive Mode |
| :--- | :--- | :--- |
| **`./aura nginx setup`** | Interactive wizard to configure a reverse proxy virtual host with SSL & firewall rules. | Supported via CLI flags |
| **`./aura nginx add-service`** | Appends an additional backend route location (e.g. `/api2/ -> :8002`) to an existing project. | Supported via CLI flags |
| **`./aura nginx enable-ssl`** | Issues and enables Let's Encrypt or Self-Signed IP certificate for an existing project by Project Code. | Supported via CLI flags |
| **`./aura nginx list`** | Displays all registered projects from the ACID-compliant SQLite state database. | Read-only |
| **`./aura nginx preview`** | Generates and displays syntax-highlighted Nginx configuration without applying to disk. | Supported via CLI flags |
| **`./aura nginx test`** | Executes `nginx -t` to validate overall syntax and configuration integrity. | Read-only |
| **`./aura nginx remove`** | Safely removes virtual host config, cleans symlinks, and reloads Nginx with automated rollback. | Supported via CLI flags |

---

### 3.2 Detailed Flag & Option Reference for `./aura nginx`

#### A. Setup Command: `./aura nginx setup`
```bash
./aura nginx setup [OPTIONS]
```

| Flag | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--project` | `-p` | `STRING` | *Prompted* | Unique project identifier name (e.g. `fastapi-prod`, `node-api`). |
| `--executable` | `-e` | `STRING` | `None` | Backend binary or startup command (e.g. `uvicorn main:app --port 8000`). |
| `--host` | `-H` | `STRING` | `127.0.0.1` | Upstream backend IP / host (e.g. `127.0.0.1`, `0.0.0.0`, or LAN IP). |
| `--port` | | `INTEGER` | `8000` | Upstream backend port number ($1–65535$). |
| `--domain` | `-d` | `STRING` | `_` (IP mode) | Domain name for virtual host (e.g. `api.example.com`). |
| `--route` | `-r` | `STRING` | `/` | Location path prefix (e.g. `/`, `/api/`, `/v1/`). |
| `--ssl / --no-ssl` | | `BOOLEAN` | `False` | Enable SSL/HTTPS on port 443 with automated HTTP-to-HTTPS 301 redirection. |
| `--self-signed` | `--ssl-ip` | `BOOLEAN` | `False` | Generate OpenSSL Self-Signed Certificate with **IP SAN** (`subjectAltName=IP:...`) for IP HTTPS. |
| `--email` | `-m` | `STRING` | `None` | Administrator email for Let's Encrypt renewal notifications. |
| `--dry-run` | | `BOOLEAN` | `False` | Simulate all operations and render configs without touching `/etc/nginx`. |
| `--non-interactive` | `-y` | `BOOLEAN` | `False` | Execute without interactive prompts using supplied flags. |

**Examples:**
```bash
# 1. Interactive Guided Wizard:
./aura nginx setup

# 2. Domain with Automated Let's Encrypt SSL:
./aura nginx setup -p api-prod -d api.domain.com --port 8000 -r / --ssl -m admin@domain.com -y

# 3. Public/LAN IP with Self-Signed IP SAN HTTPS:
./aura nginx setup -p internal-app --host 0.0.0.0 --port 5000 -r / --ssl --self-signed -y

# 4. HTTP-Only Local Proxy:
./aura nginx setup -p web-frontend --port 3000 -r / --no-ssl -y
```

---

#### B. Add Service / Route Command: `./aura nginx add-service`
```bash
./aura nginx add-service [OPTIONS]
```

| Flag | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--project` | `-p` | `STRING` | *Prompted* | Target Project Code (e.g. `SE-001`) or Project Name. |
| `--path` | `-r` | `STRING` | *Prompted* | New route location path (e.g. `/api2/`, `/ws/`, `/auth/`). |
| `--port` | | `INTEGER` | *Prompted* | Backend upstream port for this route ($1–65535$). |
| `--host` | `-H` | `STRING` | `127.0.0.1` | Upstream host IP for this route. |
| `--name` | `-n` | `STRING` | `route_<path>` | Friendly identifier name for this route. |
| `--websocket` | | `BOOLEAN` | `True` | Inject WebSocket upgrade headers (`Upgrade $http_upgrade`, `Connection "upgrade"`). |
| `--body-size` | | `STRING` | `50M` | Max request body size for this route (e.g. `10M`, `100M`). |
| `--timeout` | | `INTEGER` | `300` | Proxy read/send timeout in seconds. |
| `--strip-prefix` | | `BOOLEAN` | `False` | Strip route prefix when passing upstream (e.g. `/api2/data` $\rightarrow$ `http://upstream/data`). |

**Example:**
```bash
./aura nginx add-service --project SE-001 --path /analytics/ --port 8002 --websocket
```

---

#### C. Enable / Upgrade SSL Command: `./aura nginx enable-ssl`
```bash
./aura nginx enable-ssl [OPTIONS]
```

| Flag | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--project` | `-p` | `STRING` | *Prompted* | Project Code (e.g. `SE-001`) or project name. |
| `--domain` | `-d` | `STRING` | *From Project* | Domain name for Let's Encrypt certificate. |
| `--email` | `-m` | `STRING` | `None` | Email for Let's Encrypt account. |
| `--self-signed` | | `BOOLEAN` | `False` | Generate OpenSSL Self-Signed IP certificate instead of Let's Encrypt. |
| `--non-interactive` | `-y` | `BOOLEAN` | `False` | Run non-interactively. |

**Example:**
```bash
# Upgrade existing project SE-001 to Let's Encrypt SSL:
./aura nginx enable-ssl --project SE-001 --domain api.example.com --email admin@example.com -y
```

---

#### D. Preview Configuration Command: `./aura nginx preview`
```bash
./aura nginx preview [OPTIONS]
```

| Flag | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--project` | `-p` | `STRING` | `demo-app` | Project name to preview. |
| `--domain` | `-d` | `STRING` | `_` | Domain name to preview. |
| `--port` | | `INTEGER` | `8000` | Backend port to preview. |
| `--route` | `-r` | `STRING` | `/` | Route location path to preview. |
| `--ssl / --no-ssl` | | `BOOLEAN` | `no-ssl` | Preview with SSL directives enabled/disabled. |

**Example:**
```bash
./aura nginx preview --project my-api --domain api.domain.com --port 8000 --route / --ssl
```

---

#### E. Remove Project Command: `./aura nginx remove`
```bash
./aura nginx remove [PROJECT_NAME_OR_CODE] [OPTIONS]
```

| Flag | Short | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `PROJECT` | | `ARGUMENT` | *Prompted* | Project Code (e.g. `SE-001`) or Project Name to delete. |
| `--yes` | `-y` | `BOOLEAN` | `False` | Skip confirmation prompt. |

**Example:**
```bash
./aura nginx remove SE-001 -y
```

---

## 4. Monitoring, Scanning & Proactive Security Tools

Commands for host discovery, external API monitoring, Telegram setup, node scaling, benchmarking, and disk retention.

| Command Syntax | Underlying Script | Description & Capabilities | Supported Options / Flags |
| :--- | :--- | :--- | :--- |
| **`./aura scan`** | `scripts/scanner.py` | **Host Discovery Scanner**: Scans open TCP ports, identifies existing Nginx/Apache/Databases, resolves port collisions automatically. | `--non-interactive`, `-y`, `--auto` |
| **`./aura monitor-api`** | `scripts/monitor_api.py` | **Zero-Touch API Monitor**: Connects to existing production APIs in read-only mode to monitor Blackbox uptime, Prometheus scraping, and Loki logs without modifying existing configs. | Interactive wizard prompts for URL & paths |
| **`./aura telegram`** | `scripts/telegram_setup.py` | **1-Step Telegram Setup**: Requires only your Bot Token from `@BotFather`. Auto-detects Chat ID by polling incoming `/start` messages and configures Alertmanager. | Interactive prompt for Bot Token |
| **`./aura scale-node`** | `scripts/scale_node.py` | **Remote Node Onboarding**: Connects via SSH to remote VPS nodes, installs Node Exporter and cAdvisor, and adds targets to Master Prometheus. | Interactive prompts for IP, User, Password/Key |
| **`./aura test-load`** | `scripts/load_test.py` | **Synthetic Traffic Benchmark**: Simulates concurrent users, orders, logins, tail latency spikes, 4xx/5xx errors, and attack vectors. | `--duration <sec>` (default: 20)<br>`--rate <workers>` (default: 10)<br>`--simulate-attacks` |
| **`./aura test-alert`** | `scripts/test_alert.sh` | **Alert Test**: Dispatches a test firing alert (`TestAlertManagerDelivery`) directly to Alertmanager and Telegram. | None |
| **`./aura clean-disk`** | `scripts/auto_cleaner.sh` | **Automated Disk Cleaner**: Purges 30-day expired TSDB blocks, log buffers, Docker dangling layers, and vacuums systemd journals. | `--install-cron` (installs daily 3 AM cron)<br>`--uninstall-cron` |

---

## 5. Complete Service Deletion & Teardown Commands

Procedures to safely stop, reset, or completely delete all platform services, containers, and data.

| Teardown Level | Command Syntax | Deletion Scope & Safety Mechanism | Confirmation Required? |
| :--- | :--- | :--- | :--- |
| **1. Graceful Stop** | `./aura down` | Stops all 11 Docker containers. Preserves all metrics TSDB data, logs, traces, and Nginx configurations. | No |
| **2. Volume Reset** | `docker compose down -v` | Stops containers and wipes persistent TSDB, Loki, Tempo, and Alertmanager data volumes. | No |
| **3. Interactive Purge** | `./aura purge` | **Complete Platform Destruction**: Stops & removes all 11 containers, deletes all named volumes, removes Docker network (`monitoring_net`), prunes build caches, cleans log buffers, and offers optional Nginx site decommissioning. | **Yes** (prompts: `type 'yes' to confirm`) |
| **4. Force Teardown** | `./aura destroy -y`<br>or `./aura purge -y` | **Non-Interactive Full Teardown**: Immediately executes complete platform teardown and image/cache cleanup without confirmation prompt. | **No** (forced via `-y` / `--force`) |

---

## 6. Interactive Master Control Center (Menu Options)

Running `./aura` or `make menu` opens the interactive console with 24 dedicated options:

```text
================================================================================
 NEXTAURA MASTER CONTROL CENTER | Status: ● ALL SERVICES RUNNING (11 Active)
================================================================================

🚀 1. CORE SERVICE CONTROLS:
  [1]  Start / Deploy Observability Stack       (`aura up`)
  [2]  Restart All Containers                   (`aura restart`)
  [3]  Container Runtime Status                 (`aura status`)
  [4]  Stream Live Container Logs               (`aura logs`)

🔍 2. COMPREHENSIVE SYSTEM VIEWS:
  [5]  All-in-One Comprehensive View            (`aura view`)
  [6]  Registered Nginx Projects & Routes Table (`aura nginx list`)
  [7]  Service Access URLs & Passwords
  [8]  Run End-to-End Diagnostics Health Probe  (`aura health`)

🌐 3. NGINX REVERSE PROXY & SSL ENGINE:
  [9]  Setup New Reverse Proxy (Wizard)         (`aura nginx setup`)
  [10] Add Service / Route to Project          (`aura nginx add-service`)
  [11] Enable / Upgrade SSL (Certbot / IP SAN) (`aura nginx enable-ssl`)
  [12] Preview Nginx Configuration Syntax      (`aura nginx preview`)
  [13] Remove / Decommission Nginx Project     (`aura nginx remove`)

🛡️ 4. MONITORING, SCANNING & SECURITY:
  [14] Scan Host Ports, Services & Nginx       (`aura scan`)
  [15] Monitor Existing API / Domain           (`aura monitor-api`)
  [16] Configure 1-Step Telegram Alerts        (`aura telegram`)
  [17] Onboard Remote VPS Node via SSH         (`aura scale-node`)
  [18] Run Synthetic Traffic Benchmark         (`aura test-load`)
  [19] Dispatch Test Alert to Telegram         (`aura test-alert`)
  [20] Apply UFW Firewall & Network Hardening  (`bash scripts/security_hardening.sh`)
  [21] Run Automated 30-Day Disk Cleanup       (`aura clean-disk`)

🗑️ 5. SERVICE DELETION & DOCKER TEARDOWN:
  [22] Stop Platform Containers                (`aura down`)
  [23] Reset Platform & Wipe Volumes           (`docker compose down -v`)
  [24] ⚠️  Nuclear Purge / Delete All Services  (`aura purge`)

================================================================================
  [0]  🚪 Exit Control Center
================================================================================
```

---

## 7. Web Interfaces, Access URLs & Default Credentials

| Service | Access URL | Default Credentials | Description / Scope |
| :--- | :--- | :--- | :--- |
| **Grafana Dashboards** | `http://YOUR_VPS_IP:3000` | `admin` / `.env` password | Main visualization UI with 5 dark-mode dashboards. |
| **Nginx Ingress Proxy** | `http://YOUR_VPS_IP:80` | None | Edge gateway with dual rate-limiting zones and SSL termination. |
| **FastAPI APM Service** | `http://YOUR_VPS_IP:8000` | None | Telemetry-instrumented API with live APM spans and business metrics. |
| **FastAPI Swagger Docs** | `http://YOUR_VPS_IP:8000/docs` | None | Interactive OpenAPI endpoint explorer. |
| **Prometheus TSDB** | `http://127.0.0.1:9090` | Protected (Private) | Core time-series database and alert rule engine. |
| **Alertmanager UI** | `http://127.0.0.1:9093` | Protected (Private) | Alert grouping, deduplication, and Telegram routing. |
| **Loki Log Engine** | `http://127.0.0.1:3100` | Private | High-performance log aggregation with 30-day retention compaction. |
| **Tempo Trace Engine** | `http://127.0.0.1:3200` | Private | Distributed trace waterfall store with TraceQL engine. |

---

## 8. Pre-Provisioned Grafana Dashboards

| Dashboard Title | UID | Metrics & Key Panels |
| :--- | :--- | :--- |
| **1. Infrastructure & VPS Health Overview** | `infra-overview-v1` | CPU breakdown (User/System/IOWait), RAM usage, Root storage gauge, Disk IOPS, Network Throughput, Load Average (1m/5m/15m), and per-container resource consumption. |
| **2. FastAPI APM & API Performance** | `api-apm-performance-v1` | Requests Per Second (RPS), Status codes (2xx/4xx/5xx), $p50/p90/p95/p99$ latency curves, Top slowest routes table, In-flight concurrency gauges, and DB query latency histograms. |
| **3. Business KPIs & Usage Analytics** | `business-analytics-v1` | Real-time concurrent active users by plan tier (`free`, `pro`, `enterprise`), daily registrations, login success vs. failure ratios, token usage per client, and gross revenue metrics. |
| **4. Security, Fail2ban & Abuse Monitoring** | `security-fail2ban-v1` | Total Banned IPs, Active Fail2ban jails, Brute-force login attempts timeline, 429 rate limit triggers, 404 scanner probes, and live security event streams. |
| **5. Unified Logs & Distributed Tracing** | `logs-traces-explorer-v1` | Live Loki application log stream with log level filtering and clickable `TraceID` jumps directly into Tempo trace execution graphs. |

---

## 9. FastAPI APM & Chaos Testing Endpoints

| Endpoint | Method | Purpose & Telemetry Emitted |
| :--- | :--- | :--- |
| `/health/live` | `GET` | **Liveness Probe**: Monitored by Blackbox Exporter (`probe_success`). |
| `/health/ready` | `GET` | **Readiness Probe**: Checks simulated PostgreSQL and Redis dependencies. |
| `/metrics` | `GET` | **OpenMetrics Endpoint**: Scraped by Prometheus every 5 seconds. |
| `/api/auth/login` | `POST` | **Authentication**: Records success/failure metrics and emits JSON logs for Fail2ban. |
| `/api/auth/register` | `POST` | **User Signups**: Increments user registration counters and active users gauges. |
| `/api/checkout` | `POST` | **Revenue**: Tracks order amounts ($), currency, client token, and external Stripe span. |
| `/api/data` | `GET` | **Standard API**: Records DB `SELECT` query execution timing and client token. |
| `/api/feature/{name}` | `GET` | **Feature Analytics**: Tracks consumption per feature name and subscription tier. |
| `/api/slow` | `GET` | **Latency Chaos**: Configurable delay parameter (`?delay=0.35`) for testing $p95/p99$ latency alerts. |
| `/api/error` | `GET` | **Error Chaos**: Throws simulated status codes (`?status_code=500`) to test error rate alert rules. |
| `/api/rate-limited` | `GET` | **Rate Limit Chaos**: Returns 429 Too Many Requests to test Nginx & Fail2ban jail limits. |
| `/api/threat-simulate` | `GET` | **Security Chaos**: Simulates SQLi / path traversal scans to trigger security alert rules. |

---

## 10. Fail2ban Security Jails & Alert Rules

### Fail2ban Jails Reference
| Jail Name | Config Filter | Trigger Condition | Firewall Ban Action |
| :--- | :--- | :--- | :--- |
| **`[sshd]`** | `sshd.conf` | 3 failed SSH logins in 10 min | Bans IP for **24 Hours** + Rich Telegram alert. |
| **`[fastapi-auth]`** | `fastapi-auth.conf` | 5 failed API logins in 10 min | Bans IP for **2 Hours** + Rich Telegram alert. |
| **`[nginx-429]`** | `nginx-429.conf` | 10 rate-limit violations in 5 min | Bans IP for **1 Hour** + Rich Telegram alert. |
| **`[api-abuse]`** | `api-abuse.conf` | 3 scanner probes (`.env`, `.git`, `phpmyadmin`) | Bans IP for **24 Hours** + Rich Telegram alert. |

### Prometheus Alert Rules Reference
| Alert Rule Name | Threshold Condition | Evaluation Window | Severity |
| :--- | :--- | :--- | :--- |
| **`HostHighCpuLoad`** | CPU Load > 80% | 5m | 🔴 Critical |
| **`HostOutOfMemory`** | RAM Usage > 85% | 5m | 🔴 Critical |
| **`HostOutOfDiskSpace`** | Root Disk Usage > 90% | 5m | 🔴 Critical |
| **`HostHighLoadAverage`** | 15m Load Average > 1.5 per core | 10m | 🟡 Warning |
| **`ServiceInstanceDown`** | Target instance unreachable (`up == 0`) | 1m | 🔴 Critical |
| **`ApiHigh5xxErrorRate`** | HTTP 5xx Server Error Rate > 5% | 2m | 🔴 Critical |
| **`ApiHigh4xxErrorRate`** | HTTP 4xx Client Error Rate > 20% | 5m | 🟡 Warning |
| **`ApiHighP95Latency`** | 95th Percentile Latency > 500ms | 3m | 🟡 Warning |
| **`ApiDatabaseSlowQueries`**| p95 DB Query Latency > 200ms | 3m | 🟡 Warning |
| **`BlackboxProbeFailed`** | Synthetic HTTP 2xx check failed | 1m | 🔴 Critical |
| **`SuddenTrafficDrop`** | Incoming RPS dropped > 50% vs. last hour | 5m | 🔴 Critical |
| **`HighLoginFailureRate`**| Failed login attempts > 0.5/sec | 2m | 🔴 Critical |
| **`ApiAbuseRateLimitSpike`**| Rate limit 429 triggers > 1.0/sec | 2m | 🟡 Warning |
| **`SuspiciousTrafficBursts`**| Vulnerability scanner probes > 0.2/sec | 1m | 🔴 Critical |

---

*Manual generated for NextAura VPS Observability & Nginx DevOps Suite.*
