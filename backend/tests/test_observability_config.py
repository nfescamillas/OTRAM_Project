import json
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OBSERVABILITY_ROOT = REPOSITORY_ROOT / "observability"


def _yaml(name: str) -> dict:
    with OBSERVABILITY_ROOT.joinpath(name).open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def test_observability_is_an_independent_compose_project() -> None:
    compose = _yaml("docker-compose.yaml")

    assert compose["name"] == "otarm-observability"
    assert set(compose["services"]) == {
        "otel-collector",
        "prometheus",
        "loki",
        "tempo",
        "grafana",
    }
    assert compose["networks"]["observability"]["name"] == "otarm-observability-internal"
    assert compose["networks"]["observability"]["internal"] is True
    assert compose["networks"]["ingress"]["name"] == "otarm-observability-ingress"
    assert compose["services"]["grafana"]["ports"] == ["127.0.0.1:${GRAFANA_PORT:-3000}:3000"]
    assert all(
        "ports" not in compose["services"][service]
        for service in ("otel-collector", "prometheus", "loki", "tempo")
    )
    assert set(compose["volumes"]) == {
        "prometheus-data",
        "loki-data",
        "tempo-data",
        "grafana-data",
    }


def test_collector_routes_all_three_telemetry_signals() -> None:
    collector = _yaml("otel-collector.yaml")
    pipelines = collector["service"]["pipelines"]

    assert set(pipelines) == {"traces", "metrics", "logs"}
    assert pipelines["traces"]["exporters"] == ["otlp/tempo"]
    assert pipelines["metrics"]["exporters"] == ["prometheus"]
    assert pipelines["logs"]["exporters"] == ["otlphttp/loki"]
    assert collector["exporters"]["otlphttp/loki"]["endpoint"] == "http://loki:3100/otlp"


def test_canvas_component_creation_alert_is_actionable() -> None:
    prometheus = _yaml("prometheus.yaml")
    rules = _yaml("prometheus-rules/canvas-alerts.yaml")
    alert = rules["groups"][0]["rules"][0]

    assert prometheus["rule_files"] == ["/etc/prometheus/rules/*.yaml"]
    assert alert["alert"] == "CanvasComponentCreationRepeatedFailures"
    assert "increase(canvas_component_creation_failures_total[10m])" in alert["expr"]
    assert ">= 5" in alert["expr"]
    assert alert["for"] == "5m"
    assert alert["labels"]["owner"] == "canvas-platform"
    assert alert["labels"]["severity"] == "warning"
    for identity in ("service_name", "deployment_environment_name", "service_version"):
        assert identity in alert["expr"]
    assert set((
        "service",
        "environment",
        "deployed_version",
        "dashboard_url",
        "action",
    )).issubset(alert["annotations"])
    assert "var-environment=" in alert["annotations"]["dashboard_url"]
    assert "var-deployed_version=" in alert["annotations"]["dashboard_url"]


def test_grafana_dashboard_contains_metrics_and_deployment_filters() -> None:
    dashboard_path = OBSERVABILITY_ROOT / "grafana" / "dashboards" / "otarm-backend-metrics.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    serialized = json.dumps(dashboard)
    variables = {variable["name"]: variable for variable in dashboard["templating"]["list"]}

    assert dashboard["uid"] == "otarm-backend-metrics"
    assert variables.keys() == {"environment", "deployed_version"}
    assert "deployment_environment_name" in variables["environment"]["definition"]
    assert "service_version" in variables["deployed_version"]["definition"]
    assert all(variable["includeAll"] and variable["multi"] for variable in variables.values())

    metric_names = {
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
    assert all(metric_name in serialized for metric_name in metric_names)

    expressions = [
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel["targets"]
    ]
    assert len(expressions) == 10
    assert all("${environment:regex}" in expression for expression in expressions)
    assert all("${deployed_version:regex}" in expression for expression in expressions)

    providers_path = OBSERVABILITY_ROOT / "grafana" / "provisioning" / "dashboards" / "dashboards.yaml"
    providers = yaml.safe_load(providers_path.read_text(encoding="utf-8"))
    assert providers["providers"][0]["options"]["path"] == "/var/lib/grafana/dashboards"


def test_application_stacks_export_to_separate_observability_project() -> None:
    with REPOSITORY_ROOT.joinpath("docker-compose.yaml").open(encoding="utf-8") as compose_file:
        development = yaml.safe_load(compose_file)
    with REPOSITORY_ROOT.joinpath("docker-compose.production.yaml").open(encoding="utf-8") as compose_file:
        production = yaml.safe_load(compose_file)
    observability = _yaml("docker-compose.yaml")

    development_app = development["services"]["app"]
    production_app = production["services"]["app"]
    assert development_app["environment"]["OTEL_EXPORTER_OTLP_ENDPOINT"].endswith(
        "http://otel-collector:4318}"
    )
    assert production_app["environment"]["OTEL_EXPORTER_OTLP_ENDPOINT"].endswith(
        "http://otel-collector:4318}"
    )
    assert observability["name"] == "otarm-observability"
    for application, app in ((development, development_app), (production, production_app)):
        assert "observability" in app["networks"]
        assert application["networks"]["observability"] == {
            "name": "otarm-observability-internal",
            "external": True,
        }
