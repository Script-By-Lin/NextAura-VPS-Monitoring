import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ==============================================================================
# 1. OPENTELEMETRY TRACER INITIALIZATION
# ==============================================================================
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "fastapi-production-service")

resource = Resource.create(attributes={
    "service.name": SERVICE_NAME,
    "service.namespace": "vps-monitoring",
    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
})

tracer_provider = TracerProvider(resource=resource)

# Configure OTLP gRPC Span Exporter (non-blocking)
try:
    otlp_exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
except Exception as e:
    print(f"[Telemetry] Warning: Could not initialize OTLP Span Exporter: {e}")

trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("fastapi-instrumentor", "1.0.0")

# ==============================================================================
# 2. PROMETHEUS APPLICATION & APM METRICS
# ==============================================================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests processed",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_IN_FLIGHT_REQUESTS = Gauge(
    "http_in_flight_requests",
    "Current number of concurrent in-flight HTTP requests",
    ["endpoint"],
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query execution time in seconds",
    ["query_type", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

EXTERNAL_API_DURATION_SECONDS = Histogram(
    "external_api_duration_seconds",
    "External third-party API call latency in seconds",
    ["service", "status"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

APP_ERRORS_TOTAL = Counter(
    "app_errors_total",
    "Total count of unhandled application exceptions",
    ["type", "endpoint"],
)

# ==============================================================================
# 3. PROMETHEUS BUSINESS & SECURITY METRICS
# ==============================================================================
BUSINESS_ACTIVE_USERS_GAUGE = Gauge(
    "business_active_users_gauge",
    "Real-time concurrent active users count",
    ["plan"],
)

BUSINESS_USER_REGISTRATIONS_TOTAL = Counter(
    "business_user_registrations_total",
    "Total count of new user registrations",
    ["channel"],
)

BUSINESS_LOGIN_ATTEMPTS_TOTAL = Counter(
    "business_login_attempts_total",
    "Total user login attempts (success and failure)",
    ["status", "reason"],
)

BUSINESS_API_TOKEN_REQUESTS_TOTAL = Counter(
    "business_api_token_requests_total",
    "Total API requests segmented by client ID and tier",
    ["client_id", "tier"],
)

BUSINESS_FEATURE_USAGE_TOTAL = Counter(
    "business_feature_usage_total",
    "Total feature consumption events",
    ["feature", "tier"],
)

BUSINESS_REVENUE_AMOUNT_TOTAL = Counter(
    "business_revenue_amount_total",
    "Total revenue processed in monetary currency",
    ["currency"],
)

BUSINESS_RATE_LIMIT_HITS_TOTAL = Counter(
    "business_rate_limit_hits_total",
    "Total 429 rate limit triggers",
    ["endpoint", "client_ip"],
)

BUSINESS_SUSPICIOUS_REQUESTS_TOTAL = Counter(
    "business_suspicious_requests_total",
    "Total suspicious threat pattern requests detected",
    ["threat_type", "source_ip"],
)
