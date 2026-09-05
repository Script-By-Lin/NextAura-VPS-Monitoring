#!/usr/bin/env python3
"""
Zero-Friction Telegram Bot Auto-Setup Engine
Only requires the Bot Token from @BotFather.
Automatically discovers the bot name, auto-detects the Chat ID by polling getUpdates,
sends a verification test alert, and configures Alertmanager seamlessly.
"""

import sys
import time
import json
import urllib.request
import urllib.parse
from typing import Optional, Tuple

GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def api_call(token: str, method: str, data: Optional[dict] = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    post_data = urllib.parse.urlencode(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=post_data)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_bot_info(token: str) -> Optional[dict]:
    try:
        res = api_call(token, "getMe")
        if res.get("ok"):
            return res.get("result")
    except Exception as e:
        print(f"{RED}❌ Invalid Bot Token or Telegram API unreachable: {e}{NC}")
    return None

def auto_detect_chat_id(token: str, bot_username: str, timeout: int = 45) -> Optional[int]:
    print(f"\n{YELLOW}🔍 Auto-detecting Chat ID from your Telegram bot (@{bot_username})...{NC}")
    print(f"👉 {BOLD}Action Required:{NC} Open Telegram, search for {CYAN}@{bot_username}{NC}, and press {BOLD}/start{NC} (or send any message).")
    
    start_time = time.time()
    last_prompt = 0

    while time.time() - start_time < timeout:
        try:
            res = api_call(token, "getUpdates")
            if res.get("ok") and res.get("result"):
                # Search for latest message from result
                for item in reversed(res["result"]):
                    msg = item.get("message") or item.get("channel_post") or item.get("my_chat_member")
                    if msg:
                        chat = msg.get("chat")
                        if chat and "id" in chat:
                            chat_id = chat["id"]
                            chat_title = chat.get("first_name") or chat.get("title") or "User"
                            print(f"\n{GREEN}✅ Found incoming message from {BOLD}{chat_title}{NC} (Chat ID: {CYAN}{chat_id}{NC})!{NC}")
                            return int(chat_id)
        except Exception:
            pass

        remaining = int(timeout - (time.time() - start_time))
        if time.time() - last_prompt > 3:
            sys.stdout.write(f"\r⏳ Waiting for you to send /start to @{bot_username}... ({remaining}s remaining)")
            sys.stdout.flush()
            last_prompt = time.time()

        time.sleep(2)

    print(f"\n{YELLOW}⚠️  Timeout waiting for message. You can enter your numeric Chat ID manually or press Enter to skip.{NC}")
    manual = input("Enter Chat ID (optional): ").strip()
    return int(manual) if manual.lstrip("-").isdigit() else None

def send_connection_test(token: str, chat_id: int) -> bool:
    print(f"\n🔄 Sending test alert to Chat ID {chat_id}...")
    text = (
        "🛡️ <b>[VPS MONITORING CONNECTED ✅]</b>\n\n"
        "Your observability platform has successfully established communication with Telegram!\n\n"
        "• <b>Alert Engine:</b> Alertmanager v0.27\n"
        "• <b>Severity Badges:</b> 🔴 CRITICAL, 🟡 WARNING, 🟢 RESOLVED\n"
        "• <b>Status:</b> Active & Monitoring"
    )
    try:
        res = api_call(token, "sendMessage", {
            "chat_id": chat_id,
            "parse_mode": "HTML",
            "text": text
        })
        if res.get("ok"):
            print(f"{GREEN}🎉 Verification test message delivered to your Telegram!{NC}")
            return True
        else:
            print(f"{RED}❌ Telegram API Error: {res}{NC}")
            return False
    except Exception as e:
        print(f"{RED}❌ Failed to send Telegram message: {e}{NC}")
        return False

def configure_alertmanager(token: str, chat_id: int):
    """Writes the active Telegram config into Alertmanager and .env."""
    am_config = f"""global:
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
      - bot_token: '{token}'
        chat_id: {chat_id}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true

  - name: 'telegram-critical'
    telegram_configs:
      - bot_token: '{token}'
        chat_id: {chat_id}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true

  - name: 'telegram-warning'
    telegram_configs:
      - bot_token: '{token}'
        chat_id: {chat_id}
        parse_mode: 'HTML'
        message: '{{{{ template "telegram.default.message" . }}}}'
        send_resolved: true
"""
    with open("configs/alertmanager/alertmanager.yml", "w") as f:
        f.write(am_config)

    # Update .env if present
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
        import re
        content = re.sub(r"TELEGRAM_BOT_TOKEN=.*", f"TELEGRAM_BOT_TOKEN={token}", content)
        content = re.sub(r"TELEGRAM_CHAT_ID=.*", f"TELEGRAM_CHAT_ID={chat_id}", content)
        with open(".env", "w") as f:
            f.write(content)

    print(f"{GREEN}✓ Alertmanager & .env updated with Telegram configuration.{NC}")

def setup_telegram_wizard() -> Tuple[str, str]:
    print("\n" + "=" * 70)
    print(f"{BOLD}📲 1-STEP TELEGRAM ALERT SETUP (Token Only){NC}")
    print("=" * 70)
    print("All you need is your Bot Token from @BotFather on Telegram.")
    
    token = input("\nEnter Telegram Bot Token (from @BotFather): ").strip()
    if not token:
        print(f"{YELLOW}No token provided. Skipping Telegram setup.{NC}")
        return "", ""

    bot_info = get_bot_info(token)
    if not bot_info:
        return "", ""

    bot_name = bot_info.get("first_name", "Bot")
    bot_username = bot_info.get("username", "your_bot")
    print(f"\n{GREEN}✓ Connected to bot: {BOLD}{bot_name}{NC} (@{bot_username}){NC}")

    chat_id = auto_detect_chat_id(token, bot_username)
    if chat_id:
        send_connection_test(token, chat_id)
        configure_alertmanager(token, chat_id)
        return token, str(chat_id)
    return token, ""

if __name__ == "__main__":
    setup_telegram_wizard()
