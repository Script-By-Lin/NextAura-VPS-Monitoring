import asyncio
import time
import random
from telemetry import tracer, DB_QUERY_DURATION_SECONDS, EXTERNAL_API_DURATION_SECONDS

async def execute_db_query(query_type: str, table: str, base_delay: float = 0.015):
    """
    Simulates executing a PostgreSQL query with OpenTelemetry tracing and Prometheus metrics.
    """
    with tracer.start_as_current_span(f"db.{query_type.lower()}_{table}") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.name", "production_app_db")
        span.set_attribute("db.operation", query_type.upper())
        span.set_attribute("db.sql.table", table)

        # Simulate jitter / random latency
        jitter = random.uniform(0.005, 0.035)
        if random.random() < 0.05:
            # 5% chance of slower DB query (e.g. cold query or index scan)
            jitter += 0.15

        start_time = time.time()
        await asyncio.sleep(base_delay + jitter)
        duration = time.time() - start_time

        span.set_attribute("db.duration_seconds", duration)
        DB_QUERY_DURATION_SECONDS.labels(query_type=query_type.upper(), table=table).observe(duration)
        return {"table": table, "operation": query_type, "duration_ms": round(duration * 1000, 2)}


async def call_external_service(service: str, base_delay: float = 0.05):
    """
    Simulates calling an external third-party API (e.g. Stripe, Auth0, SendGrid).
    """
    with tracer.start_as_current_span(f"external.{service.lower()}") as span:
        span.set_attribute("peer.service", service)
        span.set_attribute("http.method", "POST")

        jitter = random.uniform(0.02, 0.08)
        start_time = time.time()
        await asyncio.sleep(base_delay + jitter)
        duration = time.time() - start_time

        status = "200" if random.random() > 0.03 else "503"
        span.set_attribute("http.status_code", status)
        span.set_attribute("rpc.duration_seconds", duration)

        EXTERNAL_API_DURATION_SECONDS.labels(service=service, status=status).observe(duration)
        return {"service": service, "status": status, "duration_ms": round(duration * 1000, 2)}
