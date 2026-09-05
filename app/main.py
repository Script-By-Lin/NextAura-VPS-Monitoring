import os
import asyncio
import random
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from middleware import ObservabilityMiddleware
from telemetry import BUSINESS_ACTIVE_USERS_GAUGE
from db_sim import execute_db_query, call_external_service
from business import (
    record_user_registration,
    record_login_attempt,
    record_transaction,
    record_feature_usage,
    record_api_token_usage,
    record_rate_limit_hit,
    record_suspicious_threat,
)
from logger import logger

app = FastAPI(
    title="Production Observability & APM FastAPI Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach APM Middleware
app.add_middleware(ObservabilityMiddleware)

# Initialize baseline active users gauge
BUSINESS_ACTIVE_USERS_GAUGE.labels(plan="free").set(120)
BUSINESS_ACTIVE_USERS_GAUGE.labels(plan="pro").set(45)
BUSINESS_ACTIVE_USERS_GAUGE.labels(plan="enterprise").set(12)

# ==============================================================================
# 1. HEALTH & METRICS SCRAPE ENDPOINTS
# ==============================================================================
@app.get("/health/live", summary="Liveness Probe")
async def liveness():
    return {"status": "UP", "service": "fastapi-production-service"}


@app.get("/health/ready", summary="Readiness Probe")
async def readiness():
    return {"status": "READY", "dependencies": {"database": "UP", "redis": "UP"}}


@app.get("/metrics", summary="Prometheus Metrics Scrape Endpoint")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==============================================================================
# 2. AUTHENTICATION & SECURITY ENDPOINTS (FAIL2BAN INTEGRATED)
# ==============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login", summary="User Login with Brute-Force Detection")
async def login(req: LoginRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Simulate authentication logic
    if req.username == "admin" and req.password == "secret123":
        record_login_attempt(True, client_ip=client_ip, user=req.username)
        return {"status": "success", "token": "jwt_token_sample_abc123", "user": req.username}
    else:
        reason = "invalid_password" if req.username == "admin" else "user_not_found"
        record_login_attempt(False, reason=reason, client_ip=client_ip, user=req.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


class RegisterRequest(BaseModel):
    username: str
    email: str
    plan: Optional[str] = "free"
    channel: Optional[str] = "organic"


@app.post("/api/auth/register", summary="User Registration")
async def register(req: RegisterRequest):
    await execute_db_query("INSERT", "users")
    record_user_registration(channel=req.channel or "organic", plan=req.plan or "free")
    return {"status": "created", "username": req.username, "plan": req.plan}


# ==============================================================================
# 3. BUSINESS & REVENUE TRANSACTIONS
# ==============================================================================
class CheckoutRequest(BaseModel):
    plan: str
    amount: float
    currency: Optional[str] = "USD"
    client_id: Optional[str] = "client_web"


@app.post("/api/checkout", summary="Process Subscription / Payment")
async def checkout(req: CheckoutRequest):
    # Step 1: Database transaction
    await execute_db_query("INSERT", "orders")

    # Step 2: Payment Gateway third-party call
    await call_external_service("stripe_gateway")

    # Step 3: Record Business Metrics
    record_transaction(amount=req.amount, currency=req.currency or "USD", plan=req.plan)
    record_api_token_usage(client_id=req.client_id or "client_web")

    return {
        "status": "completed",
        "order_id": f"ord_{random.randint(10000, 99999)}",
        "amount": req.amount,
        "currency": req.currency,
    }


# ==============================================================================
# 4. STANDARD APPLICATION DATA ROUTES
# ==============================================================================
@app.get("/api/data", summary="Query Application Data")
async def get_data(client_id: str = Query("default_client")):
    record_api_token_usage(client_id=client_id)
    db_result = await execute_db_query("SELECT", "products")
    return {
        "status": "success",
        "client_id": client_id,
        "items": [{"id": 1, "name": "Cloud Observability Suite"}, {"id": 2, "name": "VPS Security Shield"}],
        "db_meta": db_result,
    }


@app.get("/api/feature/{feature_name}", summary="Use Application Feature")
async def use_feature(feature_name: str, tier: str = Query("pro")):
    record_feature_usage(feature=feature_name, tier=tier)
    await asyncio.sleep(0.01)
    return {"status": "success", "feature": feature_name, "tier": tier}


# ==============================================================================
# 5. CHAOS & TEST ENDPOINTS (LATENCY, ERRORS, RATE LIMITS, ATTACKS)
# ==============================================================================
@app.get("/api/slow", summary="Simulate Latency Spike for p95/p99 Testing")
async def slow_endpoint(delay: float = Query(0.35, description="Delay in seconds")):
    await asyncio.sleep(delay)
    await execute_db_query("SELECT", "heavy_analytics", base_delay=0.1)
    return {"status": "slow_response_completed", "delay_applied": delay}


@app.get("/api/error", summary="Simulate 4xx / 5xx Error Response")
async def error_endpoint(status_code: int = Query(500, description="HTTP Status Code to throw")):
    if status_code >= 500:
        raise HTTPException(status_code=status_code, detail=f"Simulated server failure with status {status_code}")
    else:
        raise HTTPException(status_code=status_code, detail=f"Simulated client error with status {status_code}")


@app.get("/api/rate-limited", summary="Simulate 429 Rate Limit Exhaustion")
async def rate_limited_endpoint(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    record_rate_limit_hit("/api/rate-limited", client_ip)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please retry after 60 seconds.",
    )


@app.get("/api/threat-simulate", summary="Simulate Scanner Probe")
async def threat_simulate(request: Request, threat_type: str = Query("path_traversal")):
    client_ip = request.client.host if request.client else "127.0.0.1"
    record_suspicious_threat(threat_type=threat_type, source_ip=client_ip, endpoint=request.url.path)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Security violation detected.",
    )
