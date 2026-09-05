#!/usr/bin/env python3
"""
Host Service & Port Discovery Scanner
Scans host and Docker containers for pre-existing services (Nginx, Apache, Node.js,
Python/FastAPI, Databases, Redis, existing monitoring stacks) and generates tailored
adoption/proxy configurations to avoid port collisions and integrate existing workloads.
"""

import os
import sys
import subprocess
import socket
import re
import urllib.request
import json
from typing import Dict, List, Optional

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

WELL_KNOWN_PORTS = {
    80: ("HTTP Web Server / Reverse Proxy", ["Nginx", "Apache", "Caddy", "Traefik", "Lighttpd"]),
    443: ("HTTPS Web Server / SSL Gateway", ["Nginx", "Apache", "Caddy", "Traefik"]),
    3000: ("Web UI / Frontend / Grafana", ["Grafana", "Node.js/Next.js", "React/Vite", "Express", "Ruby on Rails"]),
    5000: ("Python/Node Backend API", ["Flask", "Gunicorn", "FastAPI", "ASP.NET Core", "Docker Registry"]),
    5173: ("Vite Frontend Dev Server", ["Vite", "Vue", "React", "Svelte"]),
    5432: ("PostgreSQL Database", ["PostgreSQL Server"]),
    6379: ("Redis In-Memory Store", ["Redis Server", "KeyDB"]),
    8000: ("Python/FastAPI Backend API", ["FastAPI", "Uvicorn", "Django", "Gunicorn", "PHP Dev Server"]),
    8080: ("Java/Node/cAdvisor Web Service", ["cAdvisor", "Spring Boot", "Tomcat", "Node.js", "Jenkins"]),
    9090: ("Prometheus Engine / Cockpit", ["Prometheus TSDB", "Cockpit Web UI"]),
    9093: ("Alertmanager Server", ["Prometheus Alertmanager"]),
    9100: ("Node Exporter", ["Prometheus Node Exporter"]),
    9115: ("Blackbox Exporter", ["Prometheus Blackbox Exporter"]),
    3100: ("Loki Log Aggregator", ["Grafana Loki"]),
    3200: ("Tempo Trace Store", ["Grafana Tempo"]),
    3306: ("MySQL / MariaDB", ["MySQL Server", "MariaDB Server"]),
    27017: ("MongoDB Database", ["MongoDB"]),
}

class ServiceInfo:
    def __init__(self, port: int, proto: str, address: str, pid: Optional[int], process_name: str, cmdline: str):
        self.port = port
        self.proto = proto
        self.address = address
        self.pid = pid
        self.process_name = process_name
        self.cmdline = cmdline
        self.category, self.candidates = WELL_KNOWN_PORTS.get(port, ("Custom Service", ["Unknown Service"]))
        self.http_banner = ""
        self.is_docker = False
        self.container_name = ""

def probe_http_banner(port: int) -> str:
    """Sends a quick HTTP HEAD request to detect server signature (e.g. nginx/1.25)."""
    try:
        url = f"http://127.0.0.1:{port}/"
        req = urllib.request.Request(url, headers={"User-Agent": "VPS-Monitoring-Discovery/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            server = resp.headers.get("Server", "")
            title = ""
            return f"HTTP {resp.status} (Server: {server})" if server else f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        server = e.headers.get("Server", "")
        return f"HTTP {e.code} (Server: {server})" if server else f"HTTP {e.code}"
    except Exception:
        return ""

def scan_listening_ports() -> List[ServiceInfo]:
    """Scans all TCP listening sockets on the host using `ss` or `/proc/net/tcp`."""
    services = []
    seen_ports = set()

    # 1. Try ss -tulpn
    try:
        output = subprocess.check_output(["ss", "-tlpn"], stderr=subprocess.DEVNULL).decode("utf-8")
        for line in output.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 4:
                local_addr = parts[3]
                match = re.search(r":(\d+)$", local_addr)
                if match:
                    port = int(match.group(1))
                    if port in seen_ports:
                        continue
                    seen_ports.add(port)

                    process_info = parts[-1] if len(parts) > 5 else ""
                    proc_match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', process_info)
                    proc_name = proc_match.group(1) if proc_match else "process"
                    pid = int(proc_match.group(2)) if proc_match else None

                    cmdline = ""
                    if pid:
                        try:
                            with open(f"/proc/{pid}/cmdline", "r") as f:
                                cmdline = f.read().replace("\x00", " ").strip()
                        except Exception:
                            pass

                    svc = ServiceInfo(port, "tcp", local_addr, pid, proc_name, cmdline)
                    svc.http_banner = probe_http_banner(port)
                    services.append(svc)
    except Exception:
        # Fallback to python socket scanning on well-known ports
        for port in WELL_KNOWN_PORTS.keys():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                svc = ServiceInfo(port, "tcp", f"127.0.0.1:{port}", None, "active_socket", "")
                svc.http_banner = probe_http_banner(port)
                services.append(svc)

    # 2. Check running Docker containers
    try:
        docker_out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Ports}}"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8")
        for line in docker_out.strip().split("\n"):
            if not line:
                continue
            cols = line.split("\t")
            if len(cols) >= 3:
                name, img, port_info = cols[0], cols[1], cols[2]
                for p_match in re.finditer(r":(\d+)->", port_info):
                    p = int(p_match.group(1))
                    for svc in services:
                        if svc.port == p:
                            svc.is_docker = True
                            svc.container_name = name
                            svc.process_name = f"docker:{name} ({img})"
    except Exception:
        pass

    services.sort(key=lambda s: s.port)
    return services

def scan_host_nginx_configs() -> Dict[str, any]:

    """Inspects /etc/nginx configuration files and systemd service status."""
    info = {
        "is_installed": False,
        "is_active_systemd": False,
        "config_files": [],
        "sites": [],
    }

    # 1. Check systemd status
    try:
        out = subprocess.check_output(["systemctl", "is-active", "nginx"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        info["is_active_systemd"] = (out == "active")
    except Exception:
        info["is_active_systemd"] = False

    # 2. Check /etc/nginx files
    nginx_dirs = ["/etc/nginx", "/etc/nginx/conf.d", "/etc/nginx/sites-enabled"]
    if os.path.exists("/etc/nginx"):
        info["is_installed"] = True
        for ndir in nginx_dirs:
            if os.path.isdir(ndir):
                for fname in os.listdir(ndir):
                    if fname.endswith(".conf") or ndir.endswith("sites-enabled"):
                        full_path = os.path.join(ndir, fname)
                        if os.path.isfile(full_path):
                            info["config_files"].append(full_path)
                            try:
                                with open(full_path, "r", errors="ignore") as f:
                                    content = f.read()
                                    server_names = re.findall(r"server_name\s+([^;]+);", content)
                                    listen_ports = re.findall(r"listen\s+([^;]+);", content)
                                    if server_names or listen_ports:
                                        info["sites"].append({
                                            "file": full_path,
                                            "domains": [s.strip() for s in server_names],
                                            "ports": [p.strip() for p in listen_ports],
                                        })
                            except Exception:
                                pass
    return info

def print_nginx_inspection_report(nginx_info: Dict[str, any], services: List[ServiceInfo]):
    print("\n" + "=" * 80)
    print(f"{BOLD}🌐 NGINX & WEB SERVER DEEP INSPECTION{NC}")
    print("=" * 80)

    # Check port 80 and 443 listeners
    p80_svc = next((s for s in services if s.port == 80), None)
    p443_svc = next((s for s in services if s.port == 443), None)

    # 1. Runtime Status
    if nginx_info["is_active_systemd"]:
        print(f"• Host Systemd Nginx:   {GREEN}ACTIVE & RUNNING{NC}")
    elif nginx_info["is_installed"]:
        print(f"• Host Systemd Nginx:   {YELLOW}INSTALLED BUT STOPPED{NC} (/etc/nginx)")
    else:
        print(f"• Host Systemd Nginx:   {CYAN}NOT INSTALLED ON HOST{NC}")

    # 2. Port Bindings
    if p80_svc:
        p80_label = f"{CYAN}{p80_svc.process_name}{NC}" if p80_svc.is_docker else f"{YELLOW}{p80_svc.process_name}{NC}"
        print(f"• Port 80 (HTTP):       {GREEN}IN USE{NC} by {p80_label}")
    else:
        print(f"• Port 80 (HTTP):       {GREEN}FREE / AVAILABLE{NC}")

    if p443_svc:
        p443_label = f"{CYAN}{p443_svc.process_name}{NC}" if p443_svc.is_docker else f"{YELLOW}{p443_svc.process_name}{NC}"
        print(f"• Port 443 (HTTPS):     {GREEN}IN USE{NC} by {p443_label}")
    else:
        print(f"• Port 443 (HTTPS):     {GREEN}FREE / AVAILABLE{NC}")

    # 3. Discovered Site Configurations
    if nginx_info["sites"]:
        print(f"\n{BOLD}📄 Discovered Host Site Configurations in /etc/nginx:{NC}")
        for site in nginx_info["sites"]:
            doms = ", ".join(site["domains"]) if site["domains"] else "default"
            ports = ", ".join(site["ports"]) if site["ports"] else "80"
            print(f"  • {site['file']} -> Domains: [{doms}] | Listening: [{ports}]")
    elif nginx_info["is_installed"]:
        print(f"\n• Host Nginx Configs:   Default template configuration found (No custom sites).")
    else:
        print(f"\n• Host Nginx Configs:   None (Clean host environment).")

def print_discovery_table(services: List[ServiceInfo]):
    """Prints the service discovery table."""
    print("\n" + "=" * 80)
    print(f"{BOLD}🔍 HOST SERVICE & PORT DISCOVERY REPORT{NC}")
    print("=" * 80)
    print(f"{'PORT':<8} {'STATUS':<12} {'CATEGORY':<32} {'PROCESS / CONTAINER':<26}")
    print("-" * 80)

    if not services:
        print(f"  {GREEN}No active listening services detected on standard ports.{NC}")
        print("=" * 80 + "\n")
        return

    for s in services:
        status_str = f"{GREEN}ACTIVE{NC}"
        banner = f" [{s.http_banner}]" if s.http_banner else ""
        proc_str = s.process_name
        if s.is_docker:
            proc_str = f"{CYAN}{s.process_name}{NC}"
        print(f"{s.port:<8} {status_str:<21} {s.category:<32} {proc_str:<26}{banner}")
    print("=" * 80 + "\n")

def get_os_info() -> Dict[str, str]:
    """Detects host operating system distribution and architecture."""
    info = {"name": "Linux", "version": "", "id": "linux", "arch": os.uname().machine}
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        info["name"] = line.strip().split("=", 1)[1].replace('"', '')
                    elif line.startswith("ID="):
                        info["id"] = line.strip().split("=", 1)[1].replace('"', '')
                    elif line.startswith("VERSION_ID="):
                        info["version"] = line.strip().split("=", 1)[1].replace('"', '')
        except Exception:
            pass
    return info

def get_system_hardware() -> Dict[str, str]:
    """Detects VPS RAM, CPU cores, disk space, and public IP."""
    import platform
    hw = {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_cores": str(os.cpu_count() or 1),
        "ram_gb": "Unknown",
        "disk_free": "Unknown",
        "public_ip": "127.0.0.1"
    }

    # RAM
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    gb = round(kb / (1024 * 1024), 1)
                    hw["ram_gb"] = f"{gb} GB"
                    break
    except Exception:
        pass

    # Disk
    try:
        stat = os.statvfs("/")
        free_gb = round((stat.f_bavail * stat.f_frsize) / (1024**3), 1)
        total_gb = round((stat.f_blocks * stat.f_frsize) / (1024**3), 1)
        hw["disk_free"] = f"{free_gb} GB free of {total_gb} GB"
    except Exception:
        pass

    # Public IP
    for url in ["https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip:
                    hw["public_ip"] = ip
                    break
        except Exception:
            continue

    return hw

def print_host_hardware_summary(os_info: Dict[str, str], hw: Dict[str, str]):
    print("\n" + "=" * 80)
    print(f"{BOLD}🖥️  VPS SYSTEM & HARDWARE SPECIFICATIONS{NC}")
    print("=" * 80)
    print(f"• Operating System: {CYAN}{os_info.get('name', 'Linux')} ({os_info.get('arch', 'x86_64')}){NC}")
    print(f"• CPU Cores:        {CYAN}{hw.get('cpu_cores')} Cores{NC}")
    print(f"• Total Memory:     {CYAN}{hw.get('ram_gb')}{NC}")
    print(f"• Root Storage:     {CYAN}{hw.get('disk_free')}{NC}")
    print(f"• Detected Public IP: {GREEN}{hw.get('public_ip')}{NC}")
    print("=" * 80)

def generate_host_nginx_snippet(grafana_port: int = 3000, fastapi_port: int = 8000) -> str:
    """Generates an Nginx server/location configuration snippet for host Nginx."""
    return f"""# ==============================================================================
# NextAura Observability Reverse Proxy Snippet for Existing Host Nginx
# Place this in /etc/nginx/conf.d/nextaura.conf or include in your server block
# ==============================================================================

# 1. Grafana Monitoring UI
location /grafana/ {{
    proxy_pass http://127.0.0.1:{grafana_port}/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}}

# 2. FastAPI Application Proxy
location /api/ {{
    proxy_pass http://127.0.0.1:{fastapi_port}/api/;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}}

# 3. FastAPI Health Checks
location /health/ {{
    proxy_pass http://127.0.0.1:{fastapi_port}/health/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}}
"""

def add_blackbox_targets(urls: List[str], prom_file: str = "configs/prometheus/prometheus.yml"):
    """Safely adds custom endpoints/domains to Prometheus Blackbox HTTP probing without modifying existing configuration."""
    if not os.path.exists(prom_file) or not urls:
        return
    try:
        with open(prom_file, "r") as f:
            content = f.read()

        added = []
        for u in urls:
            url_str = u if u.startswith("http://") or u.startswith("https://") else f"http://{u}"
            if url_str not in content:
                # Add to targets list under blackbox-http
                target_entry = f"          - '{url_str}'\n"
                if "- 'http://fastapi-app:8000/health/live'" in content:
                    content = content.replace(
                        "- 'http://fastapi-app:8000/health/live'",
                        f"- '{url_str}'\n          - 'http://fastapi-app:8000/health/live'"
                    )
                    added.append(url_str)

        if added:
            with open(prom_file, "w") as f:
                f.write(content)
            print(f"  {GREEN}✓ Added {len(added)} domain(s) to Prometheus Blackbox Uptime & SSL Monitor:{NC}")
            for a in added:
                print(f"    • {a}")
    except Exception as e:
        print(f"  {YELLOW}Warning: Could not update Blackbox targets in {prom_file}: {e}{NC}")

def add_custom_scrape_job(job_name: str, target: str, metrics_path: str = "/metrics", prom_file: str = "configs/prometheus/prometheus.yml"):
    """Safely appends a custom user service scrape job to Prometheus."""
    if not os.path.exists(prom_file):
        return
    try:
        with open(prom_file, "r") as f:
            content = f.read()

        if f"job_name: '{job_name}'" in content or target in content:
            return

        new_job = f"""
  # ----------------------------------------------------------------------------
  # Custom User Service: {job_name}
  # ----------------------------------------------------------------------------
  - job_name: '{job_name}'
    metrics_path: '{metrics_path}'
    scrape_interval: 10s
    static_configs:
      - targets: ['{target}']
        labels:
          tier: 'custom-application'
          service: '{job_name}'
"""
        content += new_job
        with open(prom_file, "w") as f:
            f.write(content)
        print(f"  {GREEN}✓ Added custom Prometheus scrape job '{job_name}' targeting {target}{metrics_path}{NC}")
    except Exception as e:
        print(f"  {YELLOW}Warning: Could not add custom scrape job: {e}{NC}")

def interactive_service_resolver(services: List[ServiceInfo], nginx_info: Optional[Dict[str, any]] = None) -> Dict[str, str]:
    """Prompts the user with tailored integration options based on discovered services.
    Guarantees that user's manual configuration is NEVER modified or overwritten.
    """
    resolutions = {}
    ports_map = {s.port: s for s in services}
    non_stack_services = [s for s in services if not s.container_name.startswith("vps-")]

    print(f"\n{GREEN}================================================================================{NC}")
    print(f"{BOLD}🛡️  SAFETY GUARANTEE: PRESERVATION OF MANUAL CONFIGURATIONS{NC}")
    print(f"{GREEN}================================================================================{NC}")
    print(f"• NextAura will {BOLD}NEVER modify, overwrite, or delete{NC} your manual configs in /etc/nginx.")
    print(f"• Your existing services and websites will continue running without interruption.")
    print(f"• NextAura will only monitor your existing services if you explicitly choose to.")
    print(f"{GREEN}================================================================================{NC}\n")

    if not non_stack_services and not (nginx_info and nginx_info.get("is_installed")):
        print(f"{GREEN}✓ Clean host environment detected. All standard ports are available!{NC}")
        return resolutions

    # 1. Check for Pre-existing Host Nginx / Reverse Proxy
    if 80 in ports_map or 443 in ports_map or (nginx_info and nginx_info.get("is_installed")):
        nginx_svc = ports_map.get(80) or ports_map.get(443)
        proc_label = nginx_svc.process_name if nginx_svc else "Host Nginx"
        
        discovered_domains = []
        if nginx_info and nginx_info.get("sites"):
            for site in nginx_info["sites"]:
                for d in site.get("domains", []):
                    if d not in ("_", "localhost", "default") and d not in discovered_domains:
                        discovered_domains.append(d)

        print(f"{BOLD}🌐 Existing Nginx / Reverse Proxy Detected ({proc_label}){NC}")
        if discovered_domains:
            print(f"• Found manual website domains: {CYAN}{', '.join(discovered_domains)}{NC}")

        print("\nHow would you like NextAura to handle your existing Nginx reverse proxy?")
        print(f"  {CYAN}[1] (Recommended) Monitor Existing Nginx & Websites:{NC}")
        print("      - Keep your /etc/nginx files 100% UNCHANGED and intact.")
        print("      - Monitor your website domains via Prometheus Blackbox (Uptime, HTTP 200, SSL expiry).")
        print("      - Stream host Nginx access logs to Loki & Fail2ban attack maps (Read-Only).")
        print("      - Run NextAura's internal Nginx on :8088 to avoid port collision with your site.")
        print("      - Generate an optional snippet file (configs/nginx_host_snippets/nextaura_proxy.conf).")
        print(f"  {CYAN}[2] Run in Isolated Mode:{NC}")
        print("      - Run NextAura on separate port (:8088) without monitoring host Nginx.")
        print(f"  {CYAN}[3] Use Default Ports :80/:443:{NC}")
        print("      - Use port 80/443 for NextAura (Only if you intend to stop your host web server).")

        choice = input("\nEnter choice [1-3] (Default: 1): ").strip() or "1"
        if choice == "1":
            resolutions["NGINX_MODE"] = "HOST_EXISTING"
            resolutions["NGINX_HTTP_PORT"] = "8088"
            resolutions["NGINX_HTTPS_PORT"] = "8443"
            
            # Ask which domains to monitor with Blackbox
            if discovered_domains:
                mon_domains = input(f"\nMonitor discovered domains [{', '.join(discovered_domains)}]? (Y/n): ").strip().lower()
                if mon_domains not in ("n", "no"):
                    add_blackbox_targets([f"http://{d}" for d in discovered_domains])
            
            # Prompt for any additional custom websites to monitor
            extra_url = input("\nEnter any other custom website URL to monitor (or press Enter to skip): ").strip()
            if extra_url:
                add_blackbox_targets([extra_url])

            snippet = generate_host_nginx_snippet(3000, 8000)
            os.makedirs("configs/nginx_host_snippets", exist_ok=True)
            with open("configs/nginx_host_snippets/nextaura_proxy.conf", "w") as f:
                f.write(snippet)
            print(f"  {GREEN}✓ Generated safe proxy snippet at: configs/nginx_host_snippets/nextaura_proxy.conf{NC}")
            print(f"  {CYAN}  (You can optionally include this in your /etc/nginx block if you wish to access Grafana at yourdomain.com/grafana/){NC}")

        elif choice == "2":
            alt_http = input("Enter alternative HTTP port for NextAura [8088]: ").strip() or "8088"
            alt_https = input("Enter alternative HTTPS port for NextAura [8443]: ").strip() or "8443"
            resolutions["NGINX_HTTP_PORT"] = alt_http
            resolutions["NGINX_HTTPS_PORT"] = alt_https
        else:
            resolutions["NGINX_HTTP_PORT"] = "80"
            resolutions["NGINX_HTTPS_PORT"] = "443"

    # 2. Check for Pre-existing Backend / API on 8000 or 5000
    if 8000 in ports_map and not ports_map[8000].container_name.startswith("vps-"):
        app_svc = ports_map[8000]
        print(f"\n{BOLD}🚀 Detected Pre-Existing Application on Port 8000 ({app_svc.process_name}){NC}")
        print("Your application will NOT be changed. How would you like NextAura to handle it?")
        print(f"  {CYAN}[1] Monitor my application with Prometheus & Blackbox (Remaps NextAura demo app to :8001){NC}")
        print(f"  {CYAN}[2] Do not monitor my application (Remaps NextAura demo app to :8001){NC}")
        choice = input("Enter choice [1-2] (Default: 1): ").strip() or "1"
        resolutions["FASTAPI_PORT"] = "8001"
        if choice == "1":
            app_metrics = input("Enter metrics endpoint path for your app [/metrics]: ").strip() or "/metrics"
            add_custom_scrape_job("user-custom-api", "host.docker.internal:8000", app_metrics)
            add_blackbox_targets(["http://host.docker.internal:8000/"])

    # 3. Check for Pre-existing Grafana / Port 3000
    if 3000 in ports_map and not ports_map[3000].container_name.startswith("vps-"):
        print(f"\n{YELLOW}[!] Detected pre-existing service on Port 3000 ({ports_map[3000].process_name}){NC}")
        print("NextAura will preserve your existing service on port 3000.")
        alt_grafana = input("Enter alternative port for NextAura Grafana [3001]: ").strip() or "3001"
        resolutions["GRAFANA_PORT"] = alt_grafana

    # 4. Check for Pre-existing Databases (Postgres 5432 / Redis 6379 / MySQL 3306)
    db_found = []
    if 5432 in ports_map: db_found.append("PostgreSQL (:5432)")
    if 6379 in ports_map: db_found.append("Redis (:6379)")
    if 3306 in ports_map: db_found.append("MySQL (:3306)")
    if 27017 in ports_map: db_found.append("MongoDB (:27017)")
    if db_found:
        print(f"\n{GREEN}✓ Detected active databases on host: {', '.join(db_found)}{NC}")
        print("  NextAura will monitor database port connectivity passively without modifying any DB data.")

    return resolutions

def find_first_available_port(start_port: int, occupied_ports: set, max_tries: int = 100) -> int:
    """Finds the first available TCP port that is neither in occupied_ports nor listening on host."""
    for p in range(start_port, start_port + max_tries):
        if p in occupied_ports:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                res = s.connect_ex(("127.0.0.1", p))
                if res != 0:
                    return p
        except Exception:
            return p
    return start_port

def auto_resolve_all_port_conflicts(services: List[ServiceInfo]) -> Dict[str, str]:
    """Automatically detects host port collisions and reassigns verified open ports."""
    resolutions = {}
    occupied_ports = {s.port for s in services if not s.container_name.startswith("vps-")}
    
    port_definitions = [
        ("GRAFANA_PORT", 3000, 3001, "Grafana Dashboards"),
        ("FASTAPI_PORT", 8000, 8001, "FastAPI APM Service"),
        ("PROMETHEUS_PORT", 9090, 9091, "Prometheus Engine"),
        ("ALERTMANAGER_PORT", 9093, 9094, "Alertmanager"),
        ("LOKI_PORT", 3100, 3101, "Loki Log Engine"),
        ("TEMPO_PORT", 3200, 3201, "Tempo Trace Engine"),
        ("NGINX_HTTP_PORT", 80, 8088, "Nginx HTTP Proxy"),
        ("NGINX_HTTPS_PORT", 443, 8443, "Nginx HTTPS Proxy"),
        ("CADVISOR_PORT", 8080, 8085, "cAdvisor Container Metrics"),
        ("NODE_EXPORTER_PORT", 9100, 9101, "Node Exporter"),
        ("BLACKBOX_PORT", 9115, 9116, "Blackbox Synthetic Prober"),
        ("OTEL_GRPC_PORT", 4317, 4327, "OpenTelemetry gRPC"),
        ("OTEL_HTTP_PORT", 4318, 4328, "OpenTelemetry HTTP"),
    ]

    adjusted = []
    for env_var, default_port, fallback_start, svc_title in port_definitions:
        if default_port in occupied_ports:
            svc_info = next((s for s in services if s.port == default_port), None)
            proc_desc = svc_info.process_name if svc_info else "Host Process"
            
            # Find next free port
            open_port = find_first_available_port(fallback_start, occupied_ports)
            occupied_ports.add(open_port)
            resolutions[env_var] = str(open_port)
            adjusted.append((svc_title, default_port, proc_desc, open_port, env_var))

    if adjusted:
        print("\n" + "=" * 80)
        print(f"{BOLD}🔄 AUTOMATIC PORT ADJUSTMENTS (PORT COLLISIONS PREVENTED){NC}")
        print("=" * 80)
        print(f"NextAura detected existing host services on standard ports.")
        print(f"Automatically assigned verified {GREEN}OPEN{NC} ports in {CYAN}.env{NC}:\n")
        print(f"{'SERVICE':<26} {'DEFAULT':<10} {'OCCUPIED BY':<22} {'ASSIGNED OPEN PORT':<20}")
        print("-" * 80)
        for svc_title, def_port, proc, open_p, env_var in adjusted:
            print(f"{svc_title:<26} :{def_port:<9} {YELLOW}{proc:<22}{NC} {GREEN}:{open_p} ({env_var}){NC}")
        print("=" * 80 + "\n")

    return resolutions

def apply_resolutions_to_env(resolutions: Dict[str, str], env_file: str = ".env"):
    """Updates .env with discovered resolutions."""
    if not resolutions:
        return
    if not os.path.exists(env_file):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", env_file)
        else:
            with open(env_file, "w") as f:
                f.write("")

    with open(env_file, "r") as f:
        lines = f.readlines()

    updated_keys = set()
    new_lines = []
    for line in lines:
        matched = False
        for k, v in resolutions.items():
            if line.startswith(f"{k}="):
                new_lines.append(f"{k}={v}\n")
                updated_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for k, v in resolutions.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_file, "w") as f:
        f.writelines(new_lines)

    print(f"\n{GREEN}✅ Applied port & configuration options to {env_file}:{NC}")
    for k, v in resolutions.items():
        print(f"  • {k}={v}")

def run_scan_workflow(interactive: bool = True):
    os_info = get_os_info()
    hw = get_system_hardware()
    print_host_hardware_summary(os_info, hw)

    print("\n🔍 Scanning host listening ports, running services, and Nginx configurations...")
    services = scan_listening_ports()
    nginx_info = scan_host_nginx_configs()
    print_nginx_inspection_report(nginx_info, services)
    print_discovery_table(services)

    # 1. Automatic port conflict resolution
    auto_resolutions = auto_resolve_all_port_conflicts(services)
    if auto_resolutions:
        apply_resolutions_to_env(auto_resolutions)

    # 2. Interactive options (if interactive)
    if interactive:
        resolutions = interactive_service_resolver(services, nginx_info)
        if resolutions:
            apply_resolutions_to_env(resolutions)
            
    return services

if __name__ == "__main__":
    is_interactive = "--non-interactive" not in sys.argv and "-y" not in sys.argv and "--auto" not in sys.argv
    run_scan_workflow(interactive=is_interactive)





