"""Phase 3c — OpenTelemetry setup is idempotent and instruments FastAPI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core import telemetry


@pytest.fixture(autouse=True)
def reset_telemetry():
    telemetry.reset_for_tests()
    yield
    telemetry.reset_for_tests()


def _make_settings(**overrides):
    from app.core.config import Settings

    base = {
        "applicationinsights_connection_string": "",
        "otel_service_name": "test-svc",
    }
    base.update(overrides)
    return Settings(**base)


def test_setup_telemetry_without_connection_string_still_runs(monkeypatch):
    # Spy on the instrumentors so we can assert they were called.
    with (
        patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app") as fa,
        patch("opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor.instrument") as hx,
    ):
        telemetry.setup_telemetry(MagicMock(), _make_settings(), engine=None)
        fa.assert_called_once()
        hx.assert_called_once()


def test_setup_telemetry_is_idempotent():
    with patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app") as fa:
        telemetry.setup_telemetry(MagicMock(), _make_settings(), engine=None)
        telemetry.setup_telemetry(MagicMock(), _make_settings(), engine=None)
        assert fa.call_count == 1


def test_setup_telemetry_with_connection_string_attaches_azure_exporter():
    fake_exporter = MagicMock()
    with (
        patch(
            "azure.monitor.opentelemetry.exporter.AzureMonitorTraceExporter.from_connection_string",
            return_value=fake_exporter,
        ) as factory,
        patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app"),
        patch("opentelemetry.instrumentation.httpx.HTTPXClientInstrumentor.instrument"),
    ):
        telemetry.setup_telemetry(
            MagicMock(),
            _make_settings(applicationinsights_connection_string="InstrumentationKey=abc"),
            engine=None,
        )
        factory.assert_called_once_with("InstrumentationKey=abc")
