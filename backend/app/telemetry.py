from __future__ import annotations

import os
import time
from importlib.metadata import PackageNotFoundError, version

from fastapi import FastAPI, Request
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _package_version() -> str:
    try:
        return version("otarm-backend")
    except PackageNotFoundError:
        return "0.1.0"


def telemetry_resource() -> Resource:
    """Build the identifying resource attached to every OTARM signal."""
    return Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "otarm-backend"),
        "deployment.environment.name": os.getenv("OTARM_ENVIRONMENT", "development"),
        "service.version": os.getenv(
            "OTARM_VERSION",
            os.getenv("RENDER_GIT_COMMIT", _package_version()),
        ),
    })


class ApplicationMetrics:
    """Low-cardinality OTARM application instruments."""

    def __init__(self, meter: Meter) -> None:
        self.http_requests = meter.create_counter(
            "otarm_http_server_requests_total", description="Completed HTTP requests."
        )
        self.http_duration = meter.create_histogram(
            "otarm_http_server_request_duration_seconds", unit="s",
            description="HTTP request duration."
        )
        self.http_active = meter.create_up_down_counter(
            "otarm_http_server_active_requests", description="HTTP requests currently being processed."
        )
        self.http_errors = meter.create_counter(
            "otarm_http_server_errors_total", description="Application errors returned by the HTTP API."
        )
        self.db_duration = meter.create_histogram(
            "otarm_db_operation_duration_seconds", unit="s", description="Database operation duration."
        )
        self.db_errors = meter.create_counter(
            "otarm_db_operation_errors_total", description="Failed database operations."
        )
        self.auth_attempts = meter.create_counter(
            "otarm_auth_attempts_total", description="Password authentication attempts."
        )
        self.authorization_denials = meter.create_counter(
            "otarm_authorization_denials_total",
            description="Authorization and separation-of-duties denials."
        )
        self.audit_events = meter.create_counter(
            "otarm_audit_events_total", description="Audit events appended by the application."
        )
        self.risk_assessments = meter.create_counter(
            "otarm_risk_assessments_total",
            description="Human-provided risk assessments recorded by the application."
        )


def _has_otlp_endpoint(signal: str) -> bool:
    return bool(
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or os.getenv(f"OTEL_EXPORTER_OTLP_{signal.upper()}_ENDPOINT")
    )


def _route(request: Request) -> str:
    route = request.scope.get("route")
    return str(getattr(route, "path", "unmatched"))


def _status_class(status_code: int) -> str:
    return f"{status_code // 100}xx"


def instrument_app(app: FastAPI) -> tuple[TracerProvider, MeterProvider, ApplicationMetrics]:
    """Instrument FastAPI and optionally export traces and metrics over OTLP/HTTP."""
    resource = telemetry_resource()
    tracer_provider = TracerProvider(resource=resource)
    if _has_otlp_endpoint("traces"):
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    metric_readers = []
    if _has_otlp_endpoint("metrics"):
        interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "60000"))
        metric_readers.append(PeriodicExportingMetricReader(
            OTLPMetricExporter(), export_interval_millis=interval
        ))
    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics = ApplicationMetrics(meter_provider.get_meter("otarm.backend"))

    @app.middleware("http")
    async def application_metrics_middleware(request: Request, call_next):
        method_attributes = {"http.request.method": request.method}
        metrics.http_active.add(1, method_attributes)
        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            attributes = {
                "http.request.method": request.method,
                "http.route": _route(request),
                "http.response.status_class": "5xx",
            }
            metrics.http_requests.add(1, attributes)
            metrics.http_duration.record(time.perf_counter() - started_at, attributes)
            metrics.http_errors.add(1, {
                "error.code": "INTERNAL",
                "http.route": attributes["http.route"],
            })
            raise
        finally:
            metrics.http_active.add(-1, method_attributes)

        attributes = {
            "http.request.method": request.method,
            "http.route": _route(request),
            "http.response.status_class": _status_class(response.status_code),
        }
        metrics.http_requests.add(1, attributes)
        metrics.http_duration.record(time.perf_counter() - started_at, attributes)
        return response

    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, meter_provider=meter_provider
    )
    app.state.tracer_provider = tracer_provider
    app.state.meter_provider = meter_provider
    app.state.metrics = metrics
    app.state.telemetry_resource = resource
    return tracer_provider, meter_provider, metrics
