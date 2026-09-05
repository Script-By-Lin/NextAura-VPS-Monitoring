#!/usr/bin/env python3
"""
NextAura VPS Monitoring & Security Platform - Interactive Master Control Center
Provides an all-in-one interactive menu for users to control, configure, scan, scale,
benchmark, and monitor their entire infrastructure from a single terminal interface.
"""

import sys
import os
import subprocess
import time
import urllib.request
import json

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

      ⚡ VPS OBSERVABILITY & SECURITY PLATFORM ⚡
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_quick_status() -> str:
    """Returns a one-line summary of container health."""
    try:
        out = subprocess.check_output(["docker-compose", "ps", "-q"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
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
    print("=" * 70)
    print(f" {BOLD}NEXTAURA MASTER CONTROL CENTER{NC} | Status: {get_quick_status()}")
    print("=" * 70)
    print(f" {CYAN}[1]{NC}  🚀 Start / Deploy Platform Stack        (`make up`)")
    print(f" {CYAN}[2]{NC}  🛑 Stop Platform Stack                  (`make down`)")
    print(f" {CYAN}[3]{NC}  🔄 Restart All Services                 (`make restart`)")
    print(f" {CYAN}[4]{NC}  🔍 Scan Host Ports, Services & Nginx    (`make scan`)")
    print(f" {CYAN}[5]{NC}  🌐 Add Custom App / Website to Nginx    (`make add-site`)")
    print(f" {CYAN}[6]{NC}  📲 Configure 1-Step Telegram Alerts     (`make telegram`)")
    print(f" {CYAN}[7]{NC}  🌐 Onboard Remote VPS Node via SSH      (`make scale-node`)")
    print(f" {CYAN}[8]{NC}  🩺 Run End-to-End Health Diagnostics    (`make healthcheck`)")
    print(f" {CYAN}[9]{NC}  🧪 Run Synthetic Traffic Benchmark      (`make test-load`)")
    print(f" {CYAN}[10]{NC} 🚨 Dispatch Test Alert to Telegram     (`make test-alert`)")
    print(f" {CYAN}[11]{NC} 🛡️ Apply UFW Firewall & Security        (`bash scripts/security_hardening.sh`)")
    print(f" {CYAN}[12]{NC} 📜 Stream Live Container Logs           (`make logs`)")
    print(f" {CYAN}[13]{NC} 🔗 Show All Service URLs & Passwords")
    print(f" {CYAN}[14]{NC} 🪄 Re-run Full Interactive Setup Wizard (`make wizard`)")
    print("=" * 70)
    print(f" {RED}[0]{NC}  🚪 Exit Control Center")
    print("=" * 70)

def show_urls():
    print("\n" + "=" * 70)
    print(f"{BOLD}🔗 NEXTAURA SERVICE ACCESS URLS & CREDENTIALS{NC}")
    print("=" * 70)
    
    # Read password from .env if present
    grafana_pass = "admin_secure_pass_change_me"
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GRAFANA_ADMIN_PASSWORD="):
                    grafana_pass = line.strip().split("=", 1)[1].strip()

    print(f"• {BOLD}Grafana Dashboards:{NC}       {CYAN}http://localhost:3000{NC} (User: admin / Pass: {grafana_pass})")
    print(f"• {BOLD}FastAPI Application:{NC}      {CYAN}http://localhost:8000{NC}")
    print(f"• {BOLD}FastAPI Swagger Docs:{NC}     {CYAN}http://localhost:8000/docs{NC}")
    print(f"• {BOLD}Prometheus Metrics:{NC}       {CYAN}http://localhost:9090{NC}")
    print(f"• {BOLD}Alertmanager UI:{NC}          {CYAN}http://localhost:9093{NC}")
    print(f"• {BOLD}Loki Log Ingestion:{NC}       {CYAN}http://localhost:3100{NC}")
    print(f"• {BOLD}Tempo Distributed Traces:{NC} {CYAN}http://localhost:3200{NC}")
    print(f"• {BOLD}Nginx Reverse Proxy:{NC}      {CYAN}http://localhost:80{NC}")
    print("=" * 70)

def run_command(cmd_list, wait=True):
    try:
        subprocess.run(cmd_list)
    except KeyboardInterrupt:
        pass
    if wait:
        input(f"\n{YELLOW}Press Enter to return to menu...{NC}")

def main():
    while True:
        print_menu()
        choice = input(f"\n{BOLD}Select an option [0-14]: {NC}").strip()

        if choice == "0":
            print(f"\n{GREEN}Goodbye! NextAura monitoring remains active in background.{NC}\n")
            break
        elif choice == "1":
            print("\n🚀 Starting all NextAura services...")
            run_command(["docker-compose", "up", "-d", "--build"])
        elif choice == "2":
            print("\n🛑 Stopping all services...")
            run_command(["docker-compose", "down"])
        elif choice == "3":
            print("\n🔄 Restarting all services...")
            run_command(["docker-compose", "restart"])
        elif choice == "4":
            run_command(["python3", "scripts/scanner.py"])
        elif choice == "5":
            run_command(["python3", "scripts/nginx_site_generator.py"])
        elif choice == "6":
            run_command(["python3", "scripts/telegram_setup.py"])
        elif choice == "7":
            run_command(["python3", "scripts/scale_node.py"])
        elif choice == "8":
            run_command(["bash", "scripts/healthcheck.sh"])
        elif choice == "9":
            duration = input("\nEnter load duration in seconds [20]: ").strip() or "20"
            rate = input("Enter concurrent workers [10]: ").strip() or "10"
            run_command(["python3", "scripts/load_test.py", "--duration", duration, "--rate", rate, "--simulate-attacks"])
        elif choice == "10":
            run_command(["bash", "scripts/test_alert.sh"])
        elif choice == "11":
            run_command(["bash", "scripts/security_hardening.sh"])
        elif choice == "12":
            print(f"\n{YELLOW}Streaming logs (Press Ctrl+C to stop)...{NC}")
            run_command(["docker-compose", "logs", "-f", "--tail=50"], wait=True)
        elif choice == "13":
            show_urls()
            input(f"\n{YELLOW}Press Enter to return to menu...{NC}")
        elif choice == "14":
            run_command(["python3", "scripts/wizard.py"])
        else:
            print(f"{RED}Invalid selection. Please enter a number between 0 and 14.{NC}")
            time.sleep(1)

if __name__ == "__main__":
    main()
