# OTARM observability stack

This directory is a standalone Docker Compose project named
`otarm-observability`. It owns its containers, volumes, and networks separately
from the development and production application stacks. Both application
projects attach only their backend container to its external, internal-only
telemetry network.

The OpenTelemetry Collector accepts OTLP/gRPC on internal port `4317` and
OTLP/HTTP on internal port `4318`. It routes traces to Tempo, makes OTLP metrics available for
Prometheus to scrape, and forwards OTLP logs to Loki. Grafana is provisioned
with all three backends as data sources and an **OTARM Backend Metrics**
dashboard.

## Start

Create a local environment file and choose a Grafana administrator password:

```powershell
Copy-Item observability/.env.example observability/.env
# Edit observability/.env and replace the password placeholder.
docker compose --env-file observability/.env -f observability/docker-compose.yaml config --quiet
docker compose --env-file observability/.env -f observability/docker-compose.yaml up -d
```

Open Grafana at `http://localhost:3000`. Its port is bound only to the host's
loopback interface. Prometheus, Loki, Tempo, and the Collector are private to
the observability networks and are reached through Grafana or by application
containers on the telemetry network.

The general OTLP endpoint enables both the backend's traces and metrics. The
collector exposes received metrics for Prometheus at its internal scrape
endpoint; they are available through the provisioned Prometheus datasource in
Grafana.

The dashboard includes all ten OTARM application metrics. Use its
**Environment** and **Deployed version** selectors to filter every panel by the
`deployment.environment.name` and `service.version` resource attributes. Both
selectors support multiple values and an **All** option.

Prometheus also loads `prometheus-rules/canvas-alerts.yaml`. The
`CanvasComponentCreationRepeatedFailures` alert fires when a single service,
environment, and deployed version records at least five component-creation
failures in ten minutes and that condition remains true for five minutes. This
filters isolated retries while surfacing a sustained failure pattern that can
prevent users from building a canvas. The alert carries the owning team,
deployment identity, a filtered dashboard link, and first-response guidance.

The committed development and production Compose definitions attach the
backend to `otarm-observability-internal` and use
`http://otel-collector:4318` by default. Deploy the observability project before
either application project so Docker has created that external network. Override
`OTEL_EXPORTER_OTLP_ENDPOINT` for development or
`OTARM_PROD_OTEL_EXPORTER_OTLP_ENDPOINT` for production when the collector runs
on another host.

## Operate and stop

```powershell
docker compose --env-file observability/.env -f observability/docker-compose.yaml ps
docker compose --env-file observability/.env -f observability/docker-compose.yaml logs -f otel-collector
docker compose --env-file observability/.env -f observability/docker-compose.yaml down
```

`down` preserves the four named data volumes. Adding `-v` permanently deletes
the local Prometheus, Loki, Tempo, and Grafana data.

This stack is intended for local development and evaluation. Grafana is the
only host-published service and remains password-protected and loopback-bound.
