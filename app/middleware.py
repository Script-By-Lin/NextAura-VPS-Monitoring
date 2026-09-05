import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from opentelemetry import trace
from telemetry import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_IN_FLIGHT_REQUESTS,
    APP_ERRORS_TOTAL,
    tracer,
)
from logger import logger

def get_normalized_endpoint(request: Request) -> str:
    """Extracts route template (e.g. /api/feature/{name}) to keep metric cardinality strictly bounded."""
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match.name == "FULL" and hasattr(route, "path"):
            return route.path
    return request.url.path


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Production-grade APM middleware providing:
    1. Low-cardinality route normalization
    2. Prometheus metric histograms & counters
    3. In-flight request concurrency gauges
    4. OpenTelemetry W3C trace context propagation
    5. Request-ID header injection
    6. Structured JSON request logging
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint = get_normalized_endpoint(request)
        method = request.method

        HTTP_IN_FLIGHT_REQUESTS.labels(endpoint=endpoint).inc()
        start_time = time.time()
        status_code = 500

        with tracer.start_as_current_span(f"{method} {endpoint}") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.client_ip", client_ip)
            span.set_attribute("http.request_id", request_id)

            try:
                response = await call_next(request)
                status_code = response.status_code
                response.headers["X-Request-ID"] = request_id

                span.set_attribute("http.status_code", status_code)
                return response
            except Exception as exc:
                APP_ERRORS_TOTAL.labels(type=exc.__class__.__name__, endpoint=endpoint).inc()
                span.record_exception(exc)
                logger.error(
                    f"Unhandled exception during {method} {endpoint}: {exc}",
                    exc_info=True,
                    extra={
                        "client_ip": client_ip,
                        "endpoint": endpoint,
                        "status_code": 500,
                    },
                )
                raise
            finally:
                duration = time.time() - start_time
                HTTP_IN_FLIGHT_REQUESTS.labels(endpoint=endpoint).dec()
                HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint, status_code=str(status_code)).observe(duration)

                # Skip excessive log spam on high-frequency internal health checks
                if endpoint not in ("/metrics", "/health/live"):
                    duration_ms = round(duration * 1000, 2)
                    log_fn = logger.info if status_code < 400 else (logger.warning if status_code < 500 else logger.error)
                    log_fn(
                        f"HTTP {method} {endpoint} -> {status_code} ({duration_ms}ms)",
                        extra={
                            "client_ip": client_ip,
                            "endpoint": endpoint,
                            "status_code": status_code,
                            "duration_ms": duration_ms,
                        },
                    )
