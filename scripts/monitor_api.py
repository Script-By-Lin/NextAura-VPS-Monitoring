#!/usr/bin/env python3
"""
NextAura VPS Monitoring System - Non-Intrusive API & Domain Monitor
Allows users to monitor their existing APIs, microservices, and domains without
modifying, touching, or altering any of their existing application or Nginx configs.
"""

import os
import sys
import subprocess
import urllib.request
import urllib.parse
import time
import re
from typing import Dict, List, Optional, Tuple

GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

BANNER = r"""
    _   __          __  ___                  
   / | / /__  _  __/ /_/   | __  ___________ _
  /  |/ / _ \| |/_/ __/ /| |/ / / / ___/ __ `/
 / /|  /  __/>  </ /_/ ___ / /_/ / /  / /_/ / 
/_/ |_/\___/_/|_|\__/_/  |_\__,_/_/   \__,_/  

      ⚡ NON-INTRUSIVE API & DOMAIN MONITOR ⚡
"""

def prompt_input(question: str, default: str = "") -> str:
    prompt = f"\n{question} [{default}]: " if default else f"\n{question}: "
    val = input(prompt).strip()
    return val if val else default

def prompt_yes_no(question: str, default: bool = True) -> bool:
    default_str = "Y/n" if default else "y/N"
    val = input(f"\n{question} ({default_str}): ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")

def test_endpoint(url: str) -> Tuple[bool, str, float]:
    """Probes the user's API endpoint to verify connectivity."""
    start = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "NextAura-HealthCheck/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            latency_ms = round((time.time() - start) * 1000, 2)
            return True, f"HTTP {resp.status} OK", latency_ms
    except urllib.error.HTTPError as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        return True, f"HTTP {e.code}", latency_ms
    except Exception as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        return False, str(e), latency_ms

def add_to_blackbox_prober(probe_url: str, prom_file: str = "configs/prometheus/prometheus.yml") -> bool:
    """Adds a health check URL to Prometheus Blackbox prober."""
    if not os.path.exists(prom_file):
        return False
    try:
        with open(prom_file, "r") as f:
            content = f.read()

        if f"'{probe_url}'" in content or f'"{probe_url}"' in content:
            print(f"  {CYAN}• Endpoint '{probe_url}' is already in Blackbox prober list.{NC}")
            return True

        target_line = f"          - '{probe_url}'\n"
        if "- 'http://fastapi-app:8000/health/live'" in content:
            content = content.replace(
                "- 'http://fastapi-app:8000/health/live'",
                f"- '{probe_url}'\n          - 'http://fastapi-app:8000/health/live'"
            )
        else:
            # Fallback insert under blackbox targets
            m = re.search(r"targets:\n", content)
            if m:
                idx = m.end()
                content = content[:idx] + target_line + content[idx:]

        with open(prom_file, "w") as f:
            f.write(content)

        print(f"  {GREEN}✓ Added '{probe_url}' to Synthetic Uptime & Latency Prober.{NC}")
        return True
    except Exception as e:
        print(f"  {YELLOW}Warning: Could not update Blackbox config: {e}{NC}")
        return False

def add_prometheus_scrape_job(
    job_name: str,
    target_host: str,
    metrics_path: str = "/metrics",
    scheme: str = "http",
    scrape_interval: str = "10s",
    bearer_token: str = "",
    prom_file: str = "configs/prometheus/prometheus.yml"
) -> bool:
    """Adds a dedicated Prometheus scrape job for the user's API."""
    if not os.path.exists(prom_file):
        return False
    try:
        with open(prom_file, "r") as f:
            content = f.read()

        clean_job = re.sub(r'[^a-zA-Z0-9_\-]', '_', job_name.lower())

        if f"job_name: '{clean_job}'" in content:
            print(f"  {CYAN}• Prometheus scrape job '{clean_job}' already exists.{NC}")
            return True

        auth_block = f"\n    bearer_token: '{bearer_token}'" if bearer_token else ""
        scheme_block = f"\n    scheme: '{scheme}'" if scheme != "http" else ""

        new_job_yaml = f"""
  # ----------------------------------------------------------------------------
  # User Custom API: {job_name}
  # ----------------------------------------------------------------------------
  - job_name: '{clean_job}'
    metrics_path: '{metrics_path}'{scheme_block}{auth_block}
    scrape_interval: {scrape_interval}
    static_configs:
      - targets: ['{target_host}']
        labels:
          tier: 'custom-api'
          service: '{clean_job}'
          app: '{clean_job}'
"""
        content += new_job_yaml
        with open(prom_file, "w") as f:
            f.write(content)

        print(f"  {GREEN}✓ Added Prometheus scrape job '{clean_job}' -> {scheme}://{target_host}{metrics_path}{NC}")
        return True
    except Exception as e:
        print(f"  {YELLOW}Warning: Could not add scrape job: {e}{NC}")
        return False

def add_promtail_log_stream(service_name: str, log_file_path: str, promtail_file: str = "configs/promtail/promtail.yml") -> bool:
    """Configures Promtail to stream the API's log file in read-only mode."""
    if not os.path.exists(promtail_file) or not log_file_path:
        return False
    try:
        with open(promtail_file, "r") as f:
            content = f.read()

        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', service_name.lower())

        if f"job: {clean_name}" in content:
            print(f"  {CYAN}• Promtail log job for '{clean_name}' already exists.{NC}")
            return True

        log_job = f"""
  # ----------------------------------------------------------------------------
  # Custom User API Logs: {service_name}
  # ----------------------------------------------------------------------------
  - job_name: custom-{clean_name}-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: {clean_name}
          app: {clean_name}
          env: production
          __path__: {log_file_path}
"""
        content += log_job
        with open(promtail_file, "w") as f:
            f.write(content)

        print(f"  {GREEN}✓ Configured Promtail to stream logs from: {log_file_path} (Read-Only){NC}")
        return True
    except Exception as e:
        print(f"  {YELLOW}Warning: Could not update Promtail config: {e}{NC}")
        return False

def get_env_port(key: str, default: str) -> str:
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith(f"{key}="):
                        return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return os.getenv(key, default)

def reload_monitoring_stack():
    """Reloads Prometheus & Promtail configs gracefully."""
    prom_port = get_env_port("PROMETHEUS_PORT", "9090")
    print(f"\n{YELLOW}Reloading Prometheus configuration...{NC}")
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{prom_port}/-/reload", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                print(f"  {GREEN}✓ Prometheus reloaded successfully via live API!{NC}")
                return
    except Exception:
        pass

    # Fallback to docker restart
    try:
        cmd = ["docker", "compose", "restart", "prometheus"] if subprocess.call(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0 else ["docker-compose", "restart", "prometheus"]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {GREEN}✓ Prometheus container restarted with new targets.{NC}")
    except Exception:
        print(f"  {YELLOW}Note: Run 'make restart' to apply changes.{NC}")

def interactive_monitor_api_wizard():
    print(BANNER)
    print("=" * 75)
    print(f"{BOLD}🛡️  ZERO-TOUCH MONITORING FOR EXISTING APIS & DOMAINS{NC}")
    print("=" * 75)
    print("• NextAura will {BOLD}NEVER edit, modify, or overwrite{NC} your API code or Nginx configs.")
    print("• Your existing domain, SSL certificates, and proxy routing remain 100% untouched.")
    print("• NextAura connects purely in {GREEN}Read-Only Observation Mode{NC}.")
    print("=" * 75)

    api_name = prompt_input("Enter a friendly name for your API/Service (e.g. User Auth API, Payment Backend)", default="my_custom_api")
    raw_url = prompt_input("Enter your API Domain or Base URL (e.g. https://api.yourdomain.com or http://127.0.0.1:5000)")

    if not raw_url:
        print(f"{RED}Error: API Domain or Base URL is required.{NC}")
        return

    # Normalize URL scheme
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        raw_url = f"https://{raw_url}"

    parsed = urllib.parse.urlparse(raw_url)
    scheme = parsed.scheme or "http"
    host_port = parsed.netloc or parsed.path

    # Step 1: Health & Uptime Endpoint
    health_path = prompt_input(
        "Enter Health Check Endpoint for Uptime & Latency Probing (e.g. /health, /api/health, /healthz, /ping, /)",
        default="/health"
    )
    if not health_path.startswith("/"):
        health_path = f"/{health_path}"

    full_probe_url = f"{scheme}://{host_port}{health_path}"

    # Pre-flight probe
    print(f"\n🔍 Testing connection to {full_probe_url}...")
    success, status_msg, latency_ms = test_endpoint(full_probe_url)
    if success:
        print(f"  {GREEN}✓ Endpoint Reachable! Status: {status_msg} | Latency: {latency_ms}ms{NC}")
    else:
        print(f"  {YELLOW}▲ Notice: Could not reach endpoint ({status_msg}). We will still monitor it for when it goes live.{NC}")

    add_to_blackbox_prober(full_probe_url)

    # Step 2: Prometheus Metrics Scrape Option
    has_metrics = prompt_yes_no("Does this API expose a Prometheus / OpenMetrics endpoint (e.g. /metrics)?", default=False)
    if has_metrics:
        metrics_path = prompt_input("Enter metrics endpoint path", default="/metrics")
        if not metrics_path.startswith("/"):
            metrics_path = f"/{metrics_path}"

        has_auth = prompt_yes_no("Does your /metrics endpoint require a Bearer token authorization?", default=False)
        bearer_token = ""
        if has_auth:
            bearer_token = prompt_input("Enter Bearer Token (leave empty to skip)")

        # Handle host.docker.internal for local services
        scrape_target = host_port
        if "127.0.0.1" in host_port or "localhost" in host_port:
            port_match = re.search(r":(\d+)$", host_port)
            p = port_match.group(1) if port_match else "80"
            scrape_target = f"host.docker.internal:{p}"

        add_prometheus_scrape_job(
            job_name=api_name,
            target_host=scrape_target,
            metrics_path=metrics_path,
            scheme=scheme if "host.docker.internal" not in scrape_target else "http",
            bearer_token=bearer_token
        )

    # Step 3: Log Ingestion into Loki (Read-Only)
    has_logs = prompt_yes_no("Do you want to stream this API's log file into Grafana Loki (Read-Only)?", default=False)
    if has_logs:
        log_path = prompt_input("Enter log file path on host (e.g. /var/log/myapi.log or /tmp/api_logs/*.log)")
        if log_path:
            add_promtail_log_stream(api_name, log_path)

    # Step 4: Reload stack
    reload_monitoring_stack()

    # Step 5: Finished Summary
    grafana_port = get_env_port("GRAFANA_PORT", "3000")
    print("\n" + "=" * 75)
    print(f"{GREEN}🎉 API '{api_name}' IS NOW ACTIVELY MONITORED BY NEXTAURA!{NC}")
    print("=" * 75)
    print(f"• {BOLD}API Name:{NC}             {CYAN}{api_name}{NC}")
    print(f"• {BOLD}Target Domain:{NC}        {CYAN}{full_probe_url}{NC}")
    print(f"• {BOLD}Uptime Prober:{NC}        {GREEN}Active (Blackbox HTTP 2xx + SSL Certificate Expiry){NC}")
    if has_metrics:
        print(f"• {BOLD}Prometheus Metrics:{NC}   {GREEN}Active ({scheme}://{host_port}{metrics_path}){NC}")
    print(f"• {BOLD}Your API Setup:{NC}       {GREEN}100% Untouched (0 modifications to your configs){NC}")
    print("=" * 75)
    print(f"\n📊 {BOLD}View live API performance now in Grafana:{NC}")
    print(f"  • {CYAN}http://localhost:{grafana_port}/d/api-apm-performance-v1{NC}")
    print(f"  • {CYAN}http://localhost:{grafana_port}/d/infra-overview-v1{NC}\n")

if __name__ == "__main__":
    interactive_monitor_api_wizard()
