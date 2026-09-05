#!/usr/bin/env python3
"""
Automated Nginx Site & Service Config Generator
Generates production-grade Nginx reverse proxy configurations for user services
(Node.js, Next.js, Python, Flask, Django, Go, PHP, frontend SPA), with rate limiting,
WebSocket support, and Let's Encrypt SSL/TLS integration.
"""

import os
import sys
import subprocess

GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

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

def generate_nginx_config(
    domain: str,
    upstream_target: str,
    service_name: str,
    enable_websocket: bool = True,
    enable_rate_limit: bool = True,
    enable_ssl: bool = False,
    ssl_cert_path: str = "",
    ssl_key_path: str = ""
) -> str:
    """Generates a complete Nginx server block configuration string."""
    clean_name = service_name.lower().replace(" ", "_").replace("-", "_")
    
    ws_block = """
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    """ if enable_websocket else """
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    """

    rate_limit_directive = "limit_req zone=api_general burst=30 nodelay;" if enable_rate_limit else ""

    if enable_ssl and ssl_cert_path and ssl_key_path:
        config = f"""# ==============================================================================
# Production Nginx Configuration for {service_name} (SSL Enabled)
# Domain: {domain} -> Upstream: {upstream_target}
# ==============================================================================

upstream {clean_name}_upstream {{
    server {upstream_target};
    keepalive 32;
}}

# HTTP -> HTTPS Redirect
server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

# HTTPS Server Block
server {{
    listen 443 ssl http2;
    server_name {domain};

    # SSL Certificates
    ssl_certificate {ssl_cert_path};
    ssl_certificate_key {ssl_key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Client Request Limits
    client_max_body_size 50M;

    # Service Reverse Proxy
    location / {{
        {rate_limit_directive}
        proxy_pass http://{clean_name}_upstream;
        {ws_block}
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    else:
        config = f"""# ==============================================================================
# Production Nginx Configuration for {service_name}
# Domain: {domain} -> Upstream: {upstream_target}
# ==============================================================================

upstream {clean_name}_upstream {{
    server {upstream_target};
    keepalive 32;
}}

server {{
    listen 80;
    server_name {domain};

    # Client Request Limits
    client_max_body_size 50M;

    # Service Reverse Proxy
    location / {{
        {rate_limit_directive}
        proxy_pass http://{clean_name}_upstream;
        {ws_block}
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    return config

def interactive_site_creator():
    print("\n" + "=" * 70)
    print(f"{BOLD}🚀 AUTOMATED NGINX SERVICE & SITE GENERATOR{NC}")
    print("=" * 70)
    print("Configure Nginx to expose and reverse-proxy your custom service / website.")

    service_name = prompt_input("Enter your service name (e.g., my_app, frontend, backend_api)", default="user_service")
    domain = prompt_input("Enter domain name or server_name (e.g. app.yourdomain.com or _)", default="_")
    upstream_target = prompt_input("Enter upstream host:port where your service is running", default="127.0.0.1:5000")
    enable_ws = prompt_yes_no("Enable WebSocket support (for Socket.io, React/Next live reload)?", default=True)
    enable_rate_limit = prompt_yes_no("Enable DDoS & rate-limiting protection zone?", default=True)
    enable_ssl = prompt_yes_no("Enable SSL / HTTPS?", default=False)

    ssl_cert = ""
    ssl_key = ""
    if enable_ssl:
        ssl_cert = prompt_input("Path to SSL certificate (.crt/.pem)", default=f"/etc/letsencrypt/live/{domain}/fullchain.pem")
        ssl_key = prompt_input("Path to SSL private key (.key)", default=f"/etc/letsencrypt/live/{domain}/privkey.pem")

    config_content = generate_nginx_config(
        domain=domain,
        upstream_target=upstream_target,
        service_name=service_name,
        enable_websocket=enable_ws,
        enable_rate_limit=enable_rate_limit,
        enable_ssl=enable_ssl,
        ssl_cert_path=ssl_cert,
        ssl_key_path=ssl_key
    )

    clean_file_name = f"{service_name.lower().replace(' ', '_')}.conf"
    target_dir = os.path.abspath("configs/nginx/conf.d")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, clean_file_name)

    with open(target_path, "w") as f:
        f.write(config_content)

    print("\n" + "=" * 70)
    print(f"{GREEN}🎉 NGINX CONFIGURATION GENERATED SUCCESSFULLY!{NC}")
    print("=" * 70)
    print(f"📁 {BOLD}Config File Path:{NC}  {CYAN}{target_path}{NC}")
    print(f"🌐 {BOLD}Routing:{NC}           http://{domain} ──► http://{upstream_target}")
    print("=" * 70)

    # Reload Nginx container if running
    try:
        reload_out = subprocess.check_output(
            ["docker", "exec", "vps-nginx-proxy", "nginx", "-s", "reload"],
            stderr=subprocess.DEVNULL
        )
        print(f"{GREEN}✓ Live Nginx container reloaded with new site config!{NC}\n")
    except Exception:
        print(f"{YELLOW}Note: Run 'make restart' or 'docker-compose restart nginx' to apply.{NC}\n")

    return target_path

if __name__ == "__main__":
    interactive_site_creator()
