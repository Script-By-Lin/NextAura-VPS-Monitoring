#!/usr/bin/env python3
"""
Fail2ban Rich Telegram Notification Engine
Performs IP Geolocation lookup, categorizes jail reasons, and formats Telegram messages
strictly matching the user-defined security template.
"""

import sys
import os
import argparse
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone

def get_env_var(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if val:
        return val
    # Fallback: check .env in repo root
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.startswith(f"{name}="):
                    return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return default

def get_ip_geo(ip: str) -> str:
    """Fetches country and city for an IP with a fast timeout."""
    if ip.startswith("127.") or ip.startswith("10.") or ip.startswith("172.") or ip.startswith("192.168."):
        return "🏠 Private / Local Network"
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,org"
        req = urllib.request.Request(url, headers={"User-Agent": "Fail2Ban-Alerter/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                country = data.get("country", "")
                city = data.get("city", "")
                org = data.get("org", "")
                parts = [p for p in [city, country, org] if p]
                return " - ".join(parts) if parts else "Unknown Region"
    except Exception:
        pass
    return "🌍 Global IP"

def get_jail_reason(jail: str, failures: int) -> str:
    jail_lower = jail.lower()
    if "fastapi-auth" in jail_lower or "auth" in jail_lower:
        return f"Brute-force authentication attack detected on protected login routes (/api/auth/login). Triggered after {failures} consecutive failed attempts."
    elif "429" in jail_lower or "rate" in jail_lower:
        return f"DDoS / API rate limit exhaustion threshold exceeded. Client issued repeated rapid bursts violating Nginx 429 rate limit zones."
    elif "abuse" in jail_lower or "scan" in jail_lower:
        return f"Malicious vulnerability scanner probe detected scanning for sensitive files (.env, .git, phpmyadmin, wp-admin)."
    elif "ssh" in jail_lower:
        return f"SSH brute-force login attack detected. Repeated unauthorized password or key authentication attempts on port 22."
    return f"Security jail policy violated with {failures} consecutive suspicious events."

def send_telegram_alert(token: str, chat_id: str, action: str, jail: str, ip: str, failures: int, bantime: str, hostname: str):
    geo_info = get_ip_geo(ip)
    reason = get_jail_reason(jail, failures)
    utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    action_label = "🚫 BANNED" if action.upper() == "BAN" else "🔓 UNBANNED"
    status_label = "IP has been blocked via iptables/nftables" if action.upper() == "BAN" else "IP ban expired / unblocked from firewall"

    message = f"""🚨 <b>SECURITY ALERT (Fail2Ban)</b>

━━━━━━━━━━━━━━━━━━
🖥 <b>Server:</b> <code>{hostname}</code>
📍 <b>Service:</b> <code>{jail}</code>
━━━━━━━━━━━━━━━━━━

🚫 <b>Action Taken:</b> <b>{action_label}</b>
🌐 <b>Source IP:</b> <code>{ip}</code>
🌍 <b>Geo:</b> {geo_info}

📊 <b>Metrics:</b>
- <b>Failed Attempts:</b> {failures}
- <b>Banned Duration:</b> {bantime}s

⏱ <b>Timestamp:</b> {utc_time}

📄 <b>Reason:</b>
<i>{reason}</i>

🔐 <b>Status:</b> {status_label}
━━━━━━━━━━━━━━━━━━"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "parse_mode": "HTML",
        "text": message
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                return True
    except Exception as e:
        print(f"Error dispatching Telegram alert: {e}", file=sys.stderr)
    return False

def main():
    parser = argparse.ArgumentParser(description="Fail2ban Telegram Dispatcher")
    parser.add_argument("--action", required=True, choices=["ban", "unban", "BAN", "UNBAN"])
    parser.add_argument("--jail", required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--failures", type=int, default=5)
    parser.add_argument("--bantime", default="3600")
    parser.add_argument("--hostname", default=os.uname().nodename)
    args = parser.parse_args()

    token = get_env_var("TELEGRAM_BOT_TOKEN")
    chat_id = get_env_var("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram Bot Token or Chat ID not configured.", file=sys.stderr)
        sys.exit(0)

    send_telegram_alert(
        token=token,
        chat_id=chat_id,
        action=args.action,
        jail=args.jail,
        ip=args.ip,
        failures=args.failures,
        bantime=args.bantime,
        hostname=args.hostname
    )

if __name__ == "__main__":
    main()
