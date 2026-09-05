#!/usr/bin/env python3
"""
Interactive Observability & Security Control System (Step 0)
Aligns with project_enhancement.md interactive control panel requirements.
"""

import os
import sys
import subprocess
import urllib.request
import urllib.parse
import json

# Add current scripts directory to path to import scanner and site generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import scanner
except ImportError:
    scanner = None

try:
    import nginx_site_generator
except ImportError:
    nginx_site_generator = None

try:
    import telegram_setup
except ImportError:
    telegram_setup = None

try:
    import monitor_api
except ImportError:
    monitor_api = None




NEXTAURA_BANNER = r"""
    _   __          __  ___                  
   / | / /__  _  __/ /_/   | __  ___________ _
  /  |/ / _ \| |/_/ __/ /| |/ / / / ___/ __ `/
 / /|  /  __/>  </ /_/ ___ / /_/ / /  / /_/ / 
/_/ |_/\___/_/|_|\__/_/  |_\__,_/_/   \__,_/  

      ⚡ VPS OBSERVABILITY & SECURITY PLATFORM ⚡
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_header(text):
    print("\n" + "=" * 70)
    print(f"🚀  {text.upper()}")
    print("=" * 70)

def prompt_choice(question, options, default_idx=0):
    print(f"\n{question}")
    for idx, opt in enumerate(options):
        marker = " (Default)" if idx == default_idx else ""
        print(f"  [{idx + 1}] {opt}{marker}")
    while True:
        choice = input(f"Enter choice [1-{len(options)}] (Enter for default): ").strip()
        if not choice:
            return options[default_idx]
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid input. Please try again.")

def prompt_input(question, default=""):
    prompt = f"\n{question} [{default}]: " if default else f"\n{question}: "
    val = input(prompt).strip()
    return val if val else default

def prompt_yes_no(question, default=True):
    default_str = "Y/n" if default else "y/N"
    val = input(f"\n{question} ({default_str}): ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes")

def main():

    clear_screen()
    print(NEXTAURA_BANNER)
    print("=" * 70)
    print("  Welcome to the NextAura VPS Monitoring & Security Platform Wizard")
    print("=" * 70)


    # --------------------------------------------------------------------------
    # 0. OS DETECTION & SYSTEM PREREQUISITES
    # --------------------------------------------------------------------------
    print_header("Step 0: OS Detection & System Prerequisites")
    os_info = scanner.get_os_info() if scanner else {"name": "Linux", "arch": "x86_64"}
    hw_info = scanner.get_system_hardware() if scanner else {"ram_gb": "8 GB", "cpu_cores": "4", "public_ip": "127.0.0.1"}
    print(f"• Detected OS:       {os_info.get('name', 'Linux')} ({os_info.get('arch', 'x86_64')})")
    print(f"• Detected Hardware: {hw_info.get('cpu_cores')} CPU Cores | {hw_info.get('ram_gb')} RAM | Public IP: {hw_info.get('public_ip')}")

    install_deps = prompt_yes_no("Verify/Install system packages (Docker, Compose, Python3, Git, UFW, Fail2ban)?", default=False)
    if install_deps and os.path.exists("scripts/install_prereqs.sh"):
        subprocess.run(["bash", "scripts/install_prereqs.sh"])

    # --------------------------------------------------------------------------
    # 0.1 SERVICE & PORT DISCOVERY SCANNER
    # --------------------------------------------------------------------------
    print_header("Step 0.1: Host Service & Port Discovery Scanner")
    scan_now = prompt_yes_no("Scan host for pre-existing services (Nginx, databases, APIs, port conflicts)?", default=True)
    if scan_now and scanner:
        scanner.run_scan_workflow(interactive=True)

    # --------------------------------------------------------------------------
    # 0.2 CUSTOM NGINX SERVICE GENERATOR
    # --------------------------------------------------------------------------
    print_header("Step 0.2: Custom Application / Website Nginx Setup")
    create_site = prompt_yes_no("Do you want to configure Nginx to reverse-proxy your own custom service/website (Node, Python, Go, PHP, SPA)?", default=False)
    if create_site and nginx_site_generator:
        nginx_site_generator.interactive_site_creator()

    # --------------------------------------------------------------------------
    # 0.3 ZERO-TOUCH EXISTING API / DOMAIN MONITORING
    # --------------------------------------------------------------------------
    print_header("Step 0.3: Existing API / Domain Monitoring (Zero-Touch Read-Only)")
    mon_api = prompt_yes_no("Do you have an existing API with its own domain/config that you want to monitor (without touching its config)?", default=False)
    if mon_api and monitor_api:
        monitor_api.interactive_monitor_api_wizard()

    # --------------------------------------------------------------------------
    # 1. ENVIRONMENT & SPECS
    # --------------------------------------------------------------------------
    print_header("Step 1: Environment & Host Infrastructure")

    deployment_target = prompt_choice(
        "Select deployment target:",
        ["Single VPS (Production)", "Multi-VPS Cluster (Federated)", "Local Machine (Dev/Testing)", "Kubernetes"],
        default_idx=0
    )
    detected_ram_str = hw_info.get("ram_gb", "8GB").replace(" ", "")
    detected_cpu_str = f"{hw_info.get('cpu_cores', '4')} Cores"
    vps_ram = prompt_input("VPS RAM", default=detected_ram_str)
    vps_cpu = prompt_input("VPS CPU Cores", default=detected_cpu_str)

    # --------------------------------------------------------------------------
    # 2. APPLICATION & TRAFFIC CONTEXT
    # --------------------------------------------------------------------------
    print_header("Step 2: Application Context & Traffic")
    backend_tech = prompt_choice(
        "Application Backend Framework:",
        ["FastAPI (Python) [Recommended]", "Node.js / Express", "Django", "Go / Gin"],
        default_idx=0
    )
    traffic_level = prompt_choice(
        "Expected API Traffic Level:",
        ["Low (< 100 RPS)", "Medium (100 - 1000 RPS)", "High (1000+ RPS)"],
        default_idx=1
    )
    use_postgres = prompt_yes_no("Enable Database Latency & Query Telemetry (PostgreSQL/MySQL)?", default=True)
    use_redis = prompt_yes_no("Enable Redis Cache & Session Telemetry?", default=True)

    # --------------------------------------------------------------------------
    # 3. TELEGRAM ALERTING CONFIGURATION (TOKEN ONLY)
    # --------------------------------------------------------------------------
    print_header("Step 3: Alerting & Telegram Bot Setup (Bot Token Only)")
    print("Alertmanager will dispatch critical infrastructure, API, and security alerts to Telegram.")
    setup_tg = prompt_yes_no("Configure Telegram instant alerting now (Requires only Bot Token from @BotFather)?", default=True)
    telegram_token = ""
    telegram_chat_id = ""
    if setup_tg and telegram_setup:
        telegram_token, telegram_chat_id = telegram_setup.setup_telegram_wizard()
    elif setup_tg:
        telegram_token = prompt_input("Enter Telegram Bot Token", default="")
        telegram_chat_id = prompt_input("Enter Telegram Chat ID", default="")


    # --------------------------------------------------------------------------
    # 4. FAIL2BAN SECURITY CONFIGURATION
    # --------------------------------------------------------------------------
    print_header("Step 4: Fail2ban & Security Hardening")
    f2b_max_retry = prompt_input("Fail2ban Max Retries before Ban", default="5")
    f2b_find_time = prompt_input("Fail2ban Find Time Window", default="600")
    f2b_ban_time = prompt_choice(
        "Fail2ban Ban Duration:",
        ["1 Hour (3600s)", "24 Hours (86400s)", "10 Minutes (600s)", "Permanent (-1)"],
        default_idx=0
    )
    ban_time_sec = "3600"
    if "24 Hours" in f2b_ban_time:
        ban_time_sec = "86400"
    elif "10 Minutes" in f2b_ban_time:
        ban_time_sec = "600"
    elif "Permanent" in f2b_ban_time:
        ban_time_sec = "-1"

    f2b_whitelist = prompt_input("IP Whitelist (space-separated)", default="127.0.0.1/8 ::1 172.28.0.0/16")

    # --------------------------------------------------------------------------
    # 5. CREDENTIALS & DEPLOYMENT STYLE
    # --------------------------------------------------------------------------
    print_header("Step 5: Credentials & Orchestration")
    grafana_user = prompt_input("Grafana Admin Username", default="admin")
    grafana_pass = prompt_input("Grafana Admin Password", default="admin_secure_pass123")

    deploy_now = prompt_yes_no("Launch Observability Stack with Docker Compose now?", default=True)

    # Write .env file
    env_content = f"""# Generated by Observability Platform Wizard
COMPOSE_PROJECT_NAME=vps_monitoring
SERVER_HOSTNAME=localhost
ENVIRONMENT=production

# Specs
VPS_RAM={vps_ram}
VPS_CPU={vps_cpu}

# Security & Credentials
GRAFANA_ADMIN_USER={grafana_user}
GRAFANA_ADMIN_PASSWORD={grafana_pass}
PROMETHEUS_BASIC_AUTH_USER=admin
PROMETHEUS_BASIC_AUTH_PASS=prom_secure_pass_change_me

# Telegram Alerting
TELEGRAM_BOT_TOKEN={telegram_token}
TELEGRAM_CHAT_ID={telegram_chat_id}

# Email Fallback
SMTP_SMARTHOST=smtp.gmail.com:587
SMTP_FROM=alerts@monitoring.local
SMTP_AUTH_USERNAME=
SMTP_AUTH_PASSWORD=
ALERT_EMAIL_TO=admin@example.com

# Service Ports
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
ALERTMANAGER_PORT=9093
LOKI_PORT=3100
TEMPO_PORT=3200
OTEL_GRPC_PORT=4317
OTEL_HTTP_PORT=4318
FASTAPI_PORT=8000
NODE_EXPORTER_PORT=9100
CADVISOR_PORT=8080
BLACKBOX_PORT=9115

# Retention Policies
PROMETHEUS_RETENTION_TIME=30d
LOKI_RETENTION_PERIOD=720h

# Fail2ban Settings
FAIL2BAN_FINDTIME={f2b_find_time}
FAIL2BAN_MAXRETRY={f2b_max_retry}
FAIL2BAN_BANTIME={ban_time_sec}
FAIL2BAN_WHITELIST={f2b_whitelist}
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("\n✅ Saved environment configuration to .env")

    # If telegram token and chat_id provided, configure Alertmanager
    if telegram_token and telegram_chat_id:
        try:
            chat_id_int = int(telegram_chat_id)
            am_cfg = f"""global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@monitoring.local'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'cluster', 'service', 'severity']
  group_wait: 10s
  group_interval: 2m
  repeat_interval: 4h
  receiver: 'telegram-default'
  routes:
    - match:
        severity: critical
      receiver: 'telegram-critical'
      group_wait: 5s
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'telegram-warning'
      group_wait: 30s
      repeat_interval: 4h

receivers:
  - name: 'telegram-default'
    telegram_configs:
      - bot_token: '{telegram_token}'
        chat_id: {chat_id_int}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true

  - name: 'telegram-critical'
    telegram_configs:
      - bot_token: '{telegram_token}'
        chat_id: {chat_id_int}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true

  - name: 'telegram-warning'
    telegram_configs:
      - bot_token: '{telegram_token}'
        chat_id: {chat_id_int}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true
"""
            with open("configs/alertmanager/alertmanager.yml", "w") as af:
                af.write(am_cfg)
            print("✅ Configured Alertmanager with Telegram receivers.")
        except Exception as e:
            print(f"Warning: Could not format Telegram config in Alertmanager: {e}")


    if deploy_now:
        print("\n🚀 Executing scripts/setup.sh...")
        subprocess.run(["bash", "scripts/setup.sh"])

if __name__ == "__main__":
    main()
