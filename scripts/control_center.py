#!/usr/bin/env python3
"""
NextAura VPS Monitoring & Nginx Automation Suite - Master Control Center
Interactive terminal console for infrastructure observability, Nginx virtual host
orchestration, comprehensive multi-views, and safe service teardown/purge.
"""

import sys
import os
import subprocess
import time
import urllib.request
import json
from typing import List, Dict, Optional

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

NGINX_ENGINE_PATH = os.path.join(REPO_ROOT, "nginx_engine")
if NGINX_ENGINE_PATH not in sys.path:
    sys.path.insert(0, NGINX_ENGINE_PATH)

GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
DIM = "\033[2m"
NC = "\033[0m"

BANNER = r"""
    _   __          __  ___                  
   / | / /__  _  __/ /_/   | __  ___________ _
  /  |/ / _ \| |/_/ __/ /| |/ / / / ___/ __ `/
 / /|  /  __/>  </ /_/ ___ / /_/ / /  / /_/ / 
/_/ |_/\___/_/|_|\__/_/  |_\__,_/_/   \__,_/  

      ⚡ VPS OBSERVABILITY & NGINX PLATFORM ⚡
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_compose_cmd() -> List[str]:
    try:
        if subprocess.call(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return ["docker", "compose"]
    except Exception:
        pass
    return ["docker-compose"]

def get_quick_status() -> str:
    """Returns a one-line summary of container health."""
    try:
        cmd = get_compose_cmd() + ["ps", "-q"]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, cwd=REPO_ROOT).decode("utf-8").strip()
        count = len(out.splitlines()) if out else 0
        if count >= 10:
            return f"{GREEN}● ALL SERVICES RUNNING ({count} Containers Active){NC}"
        elif count > 0:
            return f"{YELLOW}▲ PARTIAL ({count} Containers Active){NC}"
        else:
            return f"{RED}○ STOPPED{NC}"
    except Exception:
        return f"{YELLOW}Unknown (Docker check skipped){NC}"

def print_menu():
    clear_screen()
    print(BANNER)
    print("=" * 80)
    print(f" {BOLD}NEXTAURA MASTER CONTROL CENTER{NC} | Status: {get_quick_status()}")
    print("=" * 80)

    print(f"\n{BOLD}🚀 1. CORE SERVICE CONTROLS:{NC}")
    print(f"  {CYAN}[1]{NC}  Start / Deploy Observability Stack       (`aura up`)")
    print(f"  {CYAN}[2]{NC}  Restart All Containers                   (`aura restart`)")
    print(f"  {CYAN}[3]{NC}  Container Runtime Status                 (`aura status`)")
    print(f"  {CYAN}[4]{NC}  Stream Live Container Logs               (`aura logs`)")

    print(f"\n{BOLD}🔍 2. COMPREHENSIVE SYSTEM VIEWS:{NC}")
    print(f"  {CYAN}[5]{NC}  All-in-One Comprehensive View            (`aura view`)")
    print(f"  {CYAN}[6]{NC}  Registered Nginx Projects & Routes Table (`aura nginx list`)")
    print(f"  {CYAN}[7]{NC}  Service Access URLs & Passwords")
    print(f"  {CYAN}[8]{NC}  Run End-to-End Diagnostics Health Probe  (`aura health`)")

    print(f"\n{BOLD}🌐 3. NGINX REVERSE PROXY & SSL ENGINE:{NC}")
    print(f"  {CYAN}[9]{NC}  Setup New Reverse Proxy (Wizard)         (`aura nginx setup`)")
    print(f"  {CYAN}[10]{NC} Add Service / Route to Project          (`aura nginx add-service`)")
    print(f"  {CYAN}[11]{NC} Enable / Upgrade SSL (Certbot / IP SAN) (`aura nginx enable-ssl`)")
    print(f"  {CYAN}[12]{NC} Preview Nginx Configuration Syntax      (`aura nginx preview`)")
    print(f"  {CYAN}[13]{NC} Remove / Decommission Nginx Project     (`aura nginx remove`)")

    print(f"\n{BOLD}🛡️ 4. MONITORING, SCANNING & SECURITY:{NC}")
    print(f"  {CYAN}[14]{NC} Scan Host Ports, Services & Nginx       (`aura scan`)")
    print(f"  {CYAN}[15]{NC} Monitor Existing API / Domain           (`aura monitor-api`)")
    print(f"  {CYAN}[16]{NC} Configure 1-Step Telegram Alerts        (`aura telegram`)")
    print(f"  {CYAN}[17]{NC} Onboard Remote VPS Node via SSH         (`aura scale-node`)")
    print(f"  {CYAN}[18]{NC} Run Synthetic Traffic Benchmark         (`aura test-load`)")
    print(f"  {CYAN}[19]{NC} Dispatch Test Alert to Telegram         (`aura test-alert`)")
    print(f"  {CYAN}[20]{NC} Apply UFW Firewall & Network Hardening  (`bash scripts/security_hardening.sh`)")
    print(f"  {CYAN}[21]{NC} Run Automated 30-Day Disk Cleanup       (`aura clean-disk`)")

    print(f"\n{BOLD}🗑️ 5. SERVICE DELETION & DOCKER TEARDOWN:{NC}")
    print(f"  {YELLOW}[22]{NC} Stop Platform Containers                (`aura down`)")
    print(f"  {YELLOW}[23]{NC} Reset Platform & Wipe Volumes           (`docker compose down -v`)")
    print(f"  {RED}[24]{NC} ⚠️  Nuclear Purge / Delete All Services  (`aura purge`)")

    print("=" * 80)
    print(f"  {RED}[0]{NC}  🚪 Exit Control Center")
    print("=" * 80)

def show_urls():
    print("\n" + "=" * 80)
    print(f"{BOLD}🔗 NEXTAURA SERVICE ACCESS URLS & CREDENTIALS{NC}")
    print("=" * 80)
    
    env_vars = {
        "GRAFANA_ADMIN_PASSWORD": "admin_secure_pass_change_me",
        "GRAFANA_PORT": "3000",
        "FASTAPI_PORT": "8000",
        "PROMETHEUS_PORT": "9090",
        "ALERTMANAGER_PORT": "9093",
        "LOKI_PORT": "3100",
        "TEMPO_PORT": "3200",
        "NGINX_HTTP_PORT": "80",
    }
    env_file = os.path.join(REPO_ROOT, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                for k in env_vars.keys():
                    if line.startswith(f"{k}="):
                        env_vars[k] = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

    grafana_pass = env_vars["GRAFANA_ADMIN_PASSWORD"]
    print(f"• {BOLD}Grafana Dashboards:{NC}       {CYAN}http://localhost:{env_vars['GRAFANA_PORT']}{NC} (User: admin | Pass: {grafana_pass})")
    print(f"• {BOLD}FastAPI Application:{NC}      {CYAN}http://localhost:{env_vars['FASTAPI_PORT']}{NC}")
    print(f"• {BOLD}FastAPI Swagger Docs:{NC}     {CYAN}http://localhost:{env_vars['FASTAPI_PORT']}/docs{NC}")
    print(f"• {BOLD}Prometheus Metrics:{NC}       {CYAN}http://localhost:{env_vars['PROMETHEUS_PORT']}{NC}")
    print(f"• {BOLD}Alertmanager UI:{NC}          {CYAN}http://localhost:{env_vars['ALERTMANAGER_PORT']}{NC}")
    print(f"• {BOLD}Loki Log Ingestion:{NC}       {CYAN}http://localhost:{env_vars['LOKI_PORT']}{NC}")
    print(f"• {BOLD}Tempo Distributed Traces:{NC} {CYAN}http://localhost:{env_vars['TEMPO_PORT']}{NC}")
    print(f"• {BOLD}Nginx Ingress Proxy:{NC}      {CYAN}http://localhost:{env_vars['NGINX_HTTP_PORT']}{NC}")
    print("=" * 80)

def show_nginx_projects_view():
    print("\n" + "=" * 80)
    print(f"{BOLD}📋 REGISTERED NGINX VIRTUAL HOST PROJECTS{NC}")
    print("=" * 80)
    try:
        from utils.storage import StateManager
        mgr = StateManager()
        projects = mgr.list_projects()
        if projects:
            print(f"{'CODE':<10} {'PROJECT NAME':<20} {'DOMAIN / SERVER':<22} {'ROUTES':<18} {'SSL':<12}")
            print("-" * 80)
            for p in projects:
                ssl_badge = f"{GREEN}✓ {p.ssl_type.upper()}{NC}" if p.ssl_enabled else f"{DIM}None (HTTP){NC}"
                domain_str = p.domain if p.domain else f"Port :{p.listen_port}"
                routes_summary = ", ".join([f"{r.path}->:{r.backend_port}" for r in p.routes[:2]])
                if len(p.routes) > 2:
                    routes_summary += f" (+{len(p.routes)-2} more)"
                print(f"{CYAN}{p.project_code:<10}{NC} {p.project_name:<20} {domain_str:<22} {routes_summary:<18} {ssl_badge}")
        else:
            print(f"  {DIM}No Nginx projects registered yet. Use option [9] to configure one.{NC}")
    except Exception as e:
        print(f"  {YELLOW}Registry note: {e}{NC}")
    print("=" * 80)

def run_command(cmd_list, wait=True):
    try:
        subprocess.run(cmd_list, cwd=REPO_ROOT)
    except KeyboardInterrupt:
        pass
    if wait:
        input(f"\n{YELLOW}Press Enter to return to menu...{NC}")

def main():
    aura_bin = os.path.join(REPO_ROOT, "aura")

    while True:
        print_menu()
        choice = input(f"\n{BOLD}Select an option [0-24]: {NC}").strip()

        if choice == "0":
            print(f"\n{GREEN}Goodbye! NextAura monitoring and proxy services remain active.{NC}\n")
            break
        elif choice == "1":
            run_command([aura_bin, "up"])
        elif choice == "2":
            run_command([aura_bin, "restart"])
        elif choice == "3":
            run_command([aura_bin, "status"])
        elif choice == "4":
            print(f"\n{YELLOW}Streaming logs (Press Ctrl+C to stop)...{NC}")
            run_command([aura_bin, "logs"])
        elif choice == "5":
            run_command([aura_bin, "view"])
        elif choice == "6":
            show_nginx_projects_view()
            input(f"\n{YELLOW}Press Enter to return to menu...{NC}")
        elif choice == "7":
            show_urls()
            input(f"\n{YELLOW}Press Enter to return to menu...{NC}")
        elif choice == "8":
            run_command([aura_bin, "health"])
        elif choice == "9":
            run_command([aura_bin, "nginx", "setup"])
        elif choice == "10":
            run_command([aura_bin, "nginx", "add-service"])
        elif choice == "11":
            run_command([aura_bin, "nginx", "enable-ssl"])
        elif choice == "12":
            run_command([aura_bin, "nginx", "preview"])
        elif choice == "13":
            run_command([aura_bin, "nginx", "remove"])
        elif choice == "14":
            run_command([aura_bin, "scan"])
        elif choice == "15":
            run_command([aura_bin, "monitor-api"])
        elif choice == "16":
            run_command([aura_bin, "telegram"])
        elif choice == "17":
            run_command([aura_bin, "scale-node"])
        elif choice == "18":
            duration = input("\nEnter load duration in seconds [20]: ").strip() or "20"
            rate = input("Enter concurrent workers [10]: ").strip() or "10"
            run_command([aura_bin, "test-load", "--duration", duration, "--rate", rate, "--simulate-attacks"])
        elif choice == "19":
            run_command([aura_bin, "test-alert"])
        elif choice == "20":
            run_command(["bash", "scripts/security_hardening.sh"])
        elif choice == "21":
            run_command([aura_bin, "clean-disk"])
        elif choice == "22":
            run_command([aura_bin, "down"])
        elif choice == "23":
            print(f"\n{YELLOW}Wiping persistent TSDB/Log volumes...{NC}")
            run_command(get_compose_cmd() + ["down", "-v"])
        elif choice == "24":
            run_command([aura_bin, "purge"])
        else:
            print(f"{RED}Invalid selection. Please enter a number between 0 and 24.{NC}")
            time.sleep(1)

if __name__ == "__main__":
    main()
