#!/usr/bin/env python3
"""
Synthetic Traffic, APM & Security Attack Generator
Simulates high-fidelity production workloads to populate all Grafana dashboards:
- Infrastructure metrics (Node & Containers)
- FastAPI APM Golden Signals (RPS, Latency p50/p95/p99, Error 4xx/5xx)
- Business KPIs (Signups, Logins, Revenue, Tokens, Feature Usage)
- Security & Fail2ban (Brute-force attacks, 429 rate limits, 404 scanner probes)
"""

import asyncio
import argparse
import random
import sys
import time
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

USERS = ["alice", "bob", "charlie", "david", "eve", "admin"]
CLIENTS = ["client_ios", "client_android", "client_web", "partner_api_1", "partner_api_2"]
PLANS = ["free", "pro", "enterprise"]
FEATURES = ["csv_export", "pdf_generator", "bulk_sync", "ai_copilot", "webhook_dispatch"]
CHANNELS = ["organic", "google_ads", "referral", "product_hunt"]

async def send_request(method: str, path: str, data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    data_bytes = None
    if data:
        data_bytes = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    loop = asyncio.get_event_loop()
    try:
        def do_request():
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return resp.status, resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8")
            except Exception as e:
                return 0, str(e)

        status_code, _ = await loop.run_in_executor(None, do_request)
        return status_code
    except Exception:
        return 0

async def worker(worker_id: int, stop_event: asyncio.Event, stats: dict, simulate_attacks: bool):
    while not stop_event.is_set():
        roll = random.random()

        if roll < 0.40:
            # 1. Standard Data Request (40%)
            client = random.choice(CLIENTS)
            status = await send_request("GET", f"/api/data?client_id={client}")
            stats["data_requests"] = stats.get("data_requests", 0) + 1

        elif roll < 0.60:
            # 2. Feature Usage Request (20%)
            feature = random.choice(FEATURES)
            tier = random.choice(PLANS)
            status = await send_request("GET", f"/api/feature/{feature}?tier={tier}")
            stats["feature_requests"] = stats.get("feature_requests", 0) + 1

        elif roll < 0.75:
            # 3. Checkout / Revenue Transaction (15%)
            amount = round(random.uniform(29.0, 499.0), 2)
            plan = random.choice(["pro", "enterprise"])
            payload = {"plan": plan, "amount": amount, "currency": "USD", "client_id": random.choice(CLIENTS)}
            status = await send_request("POST", "/api/checkout", data=payload)
            stats["checkout_requests"] = stats.get("checkout_requests", 0) + 1

        elif roll < 0.85:
            # 4. Latency Spike Simulation (10%)
            delay = random.uniform(0.1, 0.4)
            status = await send_request("GET", f"/api/slow?delay={delay}")
            stats["slow_requests"] = stats.get("slow_requests", 0) + 1

        elif roll < 0.92:
            # 5. User Registration (7%)
            user = f"user_{random.randint(1000, 99999)}"
            payload = {
                "username": user,
                "email": f"{user}@example.com",
                "plan": random.choice(PLANS),
                "channel": random.choice(CHANNELS),
            }
            status = await send_request("POST", "/api/auth/register", data=payload)
            stats["registrations"] = stats.get("registrations", 0) + 1

        elif roll < 0.96:
            # 6. Error Simulation (4%)
            err_code = random.choice([400, 403, 404, 500, 503])
            status = await send_request("GET", f"/api/error?status_code={err_code}")
            stats["error_requests"] = stats.get("error_requests", 0) + 1

        else:
            # 7. Rate Limiting Simulation (4%)
            status = await send_request("GET", "/api/rate-limited")
            stats["rate_limit_hits"] = stats.get("rate_limit_hits", 0) + 1

        # Security Attacks Simulation (if enabled)
        if simulate_attacks and random.random() < 0.15:
            attack_type = random.choice(["brute_force", "threat_probe"])
            if attack_type == "brute_force":
                # Simulated failed login
                payload = {"username": "admin", "password": f"wrong_pass_{random.randint(1, 999)}"}
                status = await send_request("POST", "/api/auth/login", data=payload)
                stats["failed_logins"] = stats.get("failed_logins", 0) + 1
            else:
                threat = random.choice(["sql_injection_attempt", "path_traversal", "xss_probe"])
                status = await send_request("GET", f"/api/threat-simulate?threat_type={threat}")
                stats["threat_probes"] = stats.get("threat_probes", 0) + 1

        # Small pacing interval
        await asyncio.sleep(random.uniform(0.02, 0.08))

async def main():
    parser = argparse.ArgumentParser(description="Synthetic APM and Business Load Generator")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds (default: 30)")
    parser.add_argument("--rate", type=int, default=15, help="Number of concurrent client workers (default: 15)")
    parser.add_argument("--simulate-attacks", action="store_true", default=True, help="Simulate brute force & security probes")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print(f"🚀 Starting Synthetic Load Test ({args.duration}s @ {args.rate} concurrent workers)")
    print(f"🎯 Target URL: {BASE_URL}")
    print(f"🛡️  Security Attack Simulation: {'ENABLED' if args.simulate_attacks else 'DISABLED'}")
    print("=" * 65)

    stop_event = asyncio.Event()
    stats = {}
    tasks = [
        asyncio.create_task(worker(i, stop_event, stats, args.simulate_attacks))
        for i in range(args.rate)
    ]

    start_time = time.time()
    try:
        for remaining in range(args.duration, 0, -1):
            sys.stdout.write(f"\r⏳ Running load generation... {remaining}s remaining | Total requests: {sum(stats.values())}")
            sys.stdout.flush()
            await asyncio.sleep(1)
    finally:
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - start_time
    total_reqs = sum(stats.values())
    rps = round(total_reqs / elapsed, 2)

    print("\n\n" + "=" * 65)
    print("📊 Load Test Summary Results:")
    print("=" * 65)
    print(f"  • Total Requests Processed:  {total_reqs}")
    print(f"  • Average Request Rate:      {rps} req/sec")
    print(f"  • Data API Requests:         {stats.get('data_requests', 0)}")
    print(f"  • Feature Consumption:       {stats.get('feature_requests', 0)}")
    print(f"  • Checkout Transactions:     {stats.get('checkout_requests', 0)}")
    print(f"  • New User Signups:          {stats.get('registrations', 0)}")
    print(f"  • Slow / Latency Requests:   {stats.get('slow_requests', 0)}")
    print(f"  • Simulated Errors (4xx/5xx):{stats.get('error_requests', 0)}")
    print(f"  • Rate Limit 429 Hits:       {stats.get('rate_limit_hits', 0)}")
    print(f"  • Failed Login Attacks:      {stats.get('failed_logins', 0)}")
    print(f"  • Threat Scanner Probes:     {stats.get('threat_probes', 0)}")
    print("=" * 65)
    print("✅ Dashboards at http://localhost:3000 now display rich live telemetry!\n")

if __name__ == "__main__":
    asyncio.run(main())
