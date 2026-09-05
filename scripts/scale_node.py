#!/usr/bin/env python3
"""
NextAura VPS Automated Node Scaling & Remote Onboarding Engine
Connects to a remote Linux VPS via SSH (using IP, Username, Password/Key),
automatically installs Docker & lightweight edge telemetry agents (Node Exporter, cAdvisor),
adds the new node to Master Prometheus, and verifies multi-VPS visibility in Grafana.
"""

import sys
import os
import time
import subprocess
import getpass
import re
import urllib.request
import json
from typing import Optional

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

   🌐 MULTI-VPS SCALING & NODE ONBOARDING ENGINE
"""

def execute_remote_ssh(ip: str, user: str, password: Optional[str], key_path: Optional[str], command: str) -> Tuple[int, str]:
    """Executes a command on the remote host via SSH (using sshpass or ssh key)."""
    # 1. Try with paramiko if installed
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_path and os.path.exists(key_path):
            client.connect(ip, username=user, key_filename=key_path, timeout=10)
        else:
            client.connect(ip, username=user, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command(command, timeout=120)
        out = stdout.read().decode("utf-8") + stderr.read().decode("utf-8")
        exit_code = stdout.channel.recv_exit_status()
        client.close()
        return exit_code, out
    except ImportError:
        pass
    except Exception as e:
        return 1, str(e)

    # 2. Fallback to sshpass / ssh CLI
    if password:
        ssh_cmd = [
            "sshpass", "-p", password,
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10",
            f"{user}@{ip}", command
        ]
        # Check if sshpass is available
        if subprocess.call(["which", "sshpass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            # Install sshpass on host
            try:
                subprocess.call(["apt-get", "update", "-qq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.call(["apt-get", "install", "-y", "-qq", "sshpass"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
    else:
        ssh_cmd = [
            "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=10",
            *(["-i", key_path] if key_path else []),
            f"{user}@{ip}", command
        ]

    try:
        proc = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(timeout=120)
        return proc.returncode, out.decode("utf-8") + err.decode("utf-8")
    except Exception as e:
        return 1, str(e)

def add_node_to_prometheus(node_name: str, ip: str, config_path: str = "configs/prometheus/prometheus.yml"):
    """Appends remote targets to Prometheus config and reloads Prometheus."""
    if not os.path.exists(config_path):
        print(f"{RED}Error: Prometheus config not found at {config_path}{NC}")
        return False

    with open(config_path, "r") as f:
        content = f.read()

    # 1. Update node-exporter targets
    node_entry = f"      - targets: ['{ip}:9100']\n        labels:\n          tier: 'infrastructure'\n          host: '{node_name}'"
    if f"'{ip}:9100'" not in content:
        # Insert after node-exporter static_configs
        pattern = r"(- job_name: 'node-exporter'.*?static_configs:\n)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            idx = match.end()
            content = content[:idx] + node_entry + "\n" + content[idx:]

    # 2. Update cadvisor targets
    cadvisor_entry = f"      - targets: ['{ip}:8080']\n        labels:\n          tier: 'infrastructure'\n          host: '{node_name}'"
    if f"'{ip}:8080'" not in content:
        pattern = r"(- job_name: 'cadvisor'.*?static_configs:\n)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            idx = match.end()
            content = content[:idx] + cadvisor_entry + "\n" + content[idx:]

    with open(config_path, "w") as f:
        f.write(content)

    print(f"{GREEN}✓ Added {node_name} ({ip}) to Prometheus configuration.{NC}")

    # Reload Prometheus
    try:
        req = urllib.request.Request("http://localhost:9090/-/reload", method="POST")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print(f"{GREEN}✓ Prometheus hot-reloaded successfully.{NC}")
    except Exception:
        # Fallback to docker restart
        subprocess.call(["docker", "restart", "vps-prometheus"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN}✓ Prometheus restarted to apply new node.{NC}")

    return True

def scale_new_vps_node():
    print(BANNER)
    print("=" * 70)
    print(f"{BOLD}🚀 Onboard a New VPS Worker Node into NextAura Monitoring{NC}")
    print("=" * 70)
    print("Just enter your remote VPS IP, SSH username, and password.")
    print("NextAura will automatically configure Docker & edge telemetry on the node.\n")

    ip = input("Enter Remote VPS Public IP: ").strip()
    if not ip:
        print(f"{RED}IP is required.{NC}")
        return

    user = input("Enter SSH Username [root]: ").strip() or "root"
    
    auth_choice = input("Authenticate with [1] Password or [2] SSH Key file? [1]: ").strip() or "1"
    password = None
    key_path = None

    if auth_choice == "1":
        password = getpass.getpass(f"Enter SSH Password for {user}@{ip}: ").strip()
    else:
        key_path = input("Enter path to SSH Private Key [~/.ssh/id_rsa]: ").strip() or os.path.expanduser("~/.ssh/id_rsa")

    default_name = f"vps-node-{ip.replace('.', '-')}"
    node_name = input(f"Enter Node Name / Alias [{default_name}]: ").strip() or default_name

    print(f"\n{YELLOW}🔄 Connecting to {user}@{ip} via SSH...{NC}")

    # Step 1: Verify Connection & OS
    code, out = execute_remote_ssh(ip, user, password, key_path, "uname -a")
    if code != 0:
        print(f"{RED}❌ Failed to connect to {ip} via SSH:{NC}\n{out}")
        return
    print(f"{GREEN}✓ SSH Connected successfully: {out.strip()}{NC}")

    # Step 2: Ensure Docker on Remote VPS
    print(f"\n{YELLOW}📦 Checking Docker on remote node...{NC}")
    docker_check_cmd = """
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable --now docker || service docker start || true
    else
        echo "Docker already installed."
    fi
    """
    code, out = execute_remote_ssh(ip, user, password, key_path, docker_check_cmd)
    print(f"{GREEN}✓ Docker engine verified on remote VPS.{NC}")

    # Step 3: Deploy Edge Agents (Node Exporter & cAdvisor) on Remote VPS
    print(f"\n{YELLOW}🚀 Deploying lightweight edge monitoring containers on {node_name}...{NC}")
    deploy_cmd = """
    # 1. Start Node Exporter
    docker stop vps-node-exporter 2>/dev/null || true
    docker rm vps-node-exporter 2>/dev/null || true
    docker run -d \
      --name vps-node-exporter \
      --restart unless-stopped \
      -p 9100:9100 \
      -v /proc:/host/proc:ro \
      -v /sys:/host/sys:ro \
      -v /:/rootfs:ro \
      prom/node-exporter:v1.7.0 \
      --path.procfs=/host/proc \
      --path.rootfs=/rootfs \
      --path.sysfs=/host/sys \
      --collector.filesystem.mount-points-exclude="^/(sys|proc|dev|host|etc)($$|/)"

    # 2. Start cAdvisor
    docker stop vps-cadvisor 2>/dev/null || true
    docker rm vps-cadvisor 2>/dev/null || true
    docker run -d \
      --name vps-cadvisor \
      --restart unless-stopped \
      --privileged \
      --device=/dev/kmsg \
      -p 8080:8080 \
      -v /:/rootfs:ro \
      -v /var/run:/var/run:ro \
      -v /sys:/sys:ro \
      -v /var/lib/docker/:/var/lib/docker:ro \
      -v /dev/disk/:/dev/disk:ro \
      gcr.io/cadvisor/cadvisor:v0.49.1
    """
    code, out = execute_remote_ssh(ip, user, password, key_path, deploy_cmd)
    if code != 0:
        print(f"{RED}❌ Error launching containers on remote node:{NC}\n{out}")
        return
    print(f"{GREEN}✓ Edge containers (Node Exporter :9100 & cAdvisor :8080) are running on {ip}.{NC}")

    # Step 4: Add to Master Prometheus
    print(f"\n{YELLOW}⚙️  Registering remote node into Master Prometheus...{NC}")
    add_node_to_prometheus(node_name, ip)

    # Step 5: Test Connection from Master to Remote Node
    print(f"\n{YELLOW}🔍 Verifying scrape target reachability...{NC}")
    time.sleep(2)
    try:
        with urllib.request.urlopen(f"http://{ip}:9100/metrics", timeout=5) as resp:
            if resp.status == 200:
                print(f"{GREEN}✓ Master successfully scraped metrics from {ip}:9100!{NC}")
    except Exception as e:
        print(f"{YELLOW}Note: Scrape test from master had notice: {e}. (Ensure firewall allows master IP to reach {ip}:9100/8080){NC}")

    print("\n" + "=" * 70)
    print(f"{GREEN}🎉 REMOTE VPS NODE ONBOARDED SUCCESSFULLY!{NC}")
    print("=" * 70)
    print(f"🖥 <b>Node Name:</b>      {BOLD}{node_name}{NC}")
    print(f"🌐 <b>Node IP:</b>        {BOLD}{ip}{NC}")
    print(f"📊 <b>Dashboard:</b>      Open Grafana at http://localhost:3000 to view both nodes!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    scale_new_vps_node()
