"""OpenTelemetry wiring.

`setup_telemetry(app, settings, engine)` is called once at startup. It:

- Configures a global TracerProvider with `service.name = otel_service_name`.
- If `APPLICATIONINSIGHTS_CONNECTION_STRING` is set, attaches the Azure
  Monitor exporter so traces / metrics ship to App Insights.
- Auto-instruments FastAPI (per-request spans), SQLAlchemy (per-query
  spans) and HTTPx (per-outbound spans).

Designed to be cheap to skip: if OTel packages aren't importable, we log a
warning and continue. In tests we call it without a connection string —
spans are created but go to a no-op exporter, so assertions like
"FastAPI is instrumented" still work.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)

_already_set_up = False


def setup_telemetry(app: Any, settings: Settings, engine: Any | None = None) -> None:
    """Idempotent: safe to call multiple times (no-op after the first)."""
    global _already_set_up
    if _already_set_up:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
    except ImportError as exc:
        log.warning("otel_unavailable", error=str(exc))
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    conn = settings.applicationinsights_connection_string
    if conn:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            exporter = AzureMonitorTraceExporter.from_connection_string(conn)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            log.info("otel_azure_monitor_enabled")
        except Exception as exc:
            log.warning("otel_azure_monitor_skipped", error=str(exc))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    _already_set_up = True
    log.info(
        "otel_setup_done",
        service=settings.otel_service_name,
        azure_monitor=bool(conn),
    )


def reset_for_tests() -> None:
    """Allow tests to re-run setup_telemetry with a fresh provider."""
    global _already_set_up
    _already_set_up = False
