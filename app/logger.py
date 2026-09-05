import logging
import sys
import os
import json
from datetime import datetime, timezone
from opentelemetry import trace

LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/var/log/fastapi/app.log")

class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON including active OpenTelemetry TraceID/SpanID."""

    def format(self, record: logging.LogRecord) -> str:
        current_span = trace.get_current_span()
        span_context = current_span.get_span_context() if current_span else None

        trace_id = ""
        span_id = ""
        if span_context and span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")

        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", trace_id),
            "span_id": getattr(record, "span_id", span_id),
            "client_ip": getattr(record, "client_ip", "127.0.0.1"),
            "endpoint": getattr(record, "endpoint", "-"),
            "status_code": getattr(record, "status_code", 0),
            "duration_ms": getattr(record, "duration_ms", 0.0),
        }

        # Include custom extra fields if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload.update(record.extra_data)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logger(name: str = "fastapi-service") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = StructuredJsonFormatter()

    # 1. Console Stream Handler (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler for Promtail ingestion
    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE_PATH)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[Logger] Warning: Could not initialize log file at {LOG_FILE_PATH}: {e}")

    return logger

logger = setup_logger()
