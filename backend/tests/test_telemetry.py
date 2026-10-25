from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider

from app.main import create_app
from app.telemetry import ApplicationMetrics, telemetry_resource


def test_telemetry_resource_identifies_deployment(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "otarm-api")
    monkeypatch.setenv("OTARM_ENVIRONMENT", "staging")
    monkeypatch.setenv("OTARM_VERSION", "sha-abc123")

    attributes = telemetry_resource().attributes

    assert attributes["service.name"] == "otarm-api"
    assert attributes["deployment.environment.name"] == "staging"
    assert attributes["service.version"] == "sha-abc123"


def test_app_is_instrumented_with_development_defaults(monkeypatch) -> None:
    for variable in ("OTEL_SERVICE_NAME", "OTARM_ENVIRONMENT", "OTARM_VERSION", "RENDER_GIT_COMMIT"):
        monkeypatch.delenv(variable, raising=False)

    app = create_app(database_url="sqlite:///:memory:")

    provider = app.state.tracer_provider
    assert isinstance(provider, TracerProvider)
    assert provider.resource.attributes["service.name"] == "otarm-backend"
    assert provider.resource.attributes["deployment.environment.name"] == "development"
    assert provider.resource.attributes["service.version"] == "0.1.0"
    assert isinstance(app.state.meter_provider, MeterProvider)


def test_recommended_metrics_include_deployment_resource(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "otarm-api")
    monkeypatch.setenv("OTARM_ENVIRONMENT", "production")
    monkeypatch.setenv("OTARM_VERSION", "sha-deployed")
    reader = InMemoryMetricReader()
    provider = MeterProvider(resource=telemetry_resource(), metric_readers=[reader])
    metrics = ApplicationMetrics(provider.get_meter("test"))

    metrics.http_requests.add(1, {"http.route": "/healthz"})
    metrics.http_duration.record(0.01, {"http.route": "/healthz"})
    metrics.http_active.add(1, {"http.request.method": "GET"})
    metrics.db_duration.record(0.01, {"db.operation.name": "SELECT"})
    metrics.db_errors.add(1, {"db.operation.name": "SELECT"})
    metrics.http_errors.add(1, {"error.code": "VALIDATION"})
    metrics.auth_attempts.add(1, {"result": "success"})
    metrics.authorization_denials.add(1, {"reason": "role"})
    metrics.audit_events.add(1, {"event.type": "ASSET_CREATED"})
    metrics.risk_assessments.add(1, {"status": "completed"})

    exported = reader.get_metrics_data()
    resource_metrics = exported.resource_metrics[0]
    names = {
        metric.name
        for scope in resource_metrics.scope_metrics
        for metric in scope.metrics
    }

    assert names == {
        "otarm_http_server_requests_total",
        "otarm_http_server_request_duration_seconds",
        "otarm_http_server_active_requests",
        "otarm_http_server_errors_total",
        "otarm_db_operation_duration_seconds",
        "otarm_db_operation_errors_total",
        "otarm_auth_attempts_total",
        "otarm_authorization_denials_total",
        "otarm_audit_events_total",
        "otarm_risk_assessments_total",
    }
    assert resource_metrics.resource.attributes["service.name"] == "otarm-api"
    assert resource_metrics.resource.attributes["deployment.environment.name"] == "production"
    assert resource_metrics.resource.attributes["service.version"] == "sha-deployed"
    provider.shutdown()
