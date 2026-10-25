# OTARM FastAPI backend

Implements the root [`openapi.yaml`](../openapi.yaml) contract with a SQLAlchemy repository supporting PostgreSQL and SQLite. Records persist across process restarts.

## Run locally

Set a demo password at runtime; no password is committed to the repository.

```powershell
cd backend
$env:OTARM_DEMO_PASSWORD = "choose-a-local-demo-password"
$env:OTARM_DATABASE_URL = "sqlite:///./otarm.db"
uv sync --dev
uv run python -m uvicorn app.main:app --reload --port 8000
```

`OTARM_DATABASE_URL` accepts a SQLAlchemy database URL. If it is omitted, the application uses `backend/otarm.db`. PostgreSQL connections use Psycopg 3; both `postgresql://` and the provider-style `postgres://` URL prefix are normalized to the explicit `postgresql+psycopg://` dialect.

Example PostgreSQL configuration:

```powershell
$env:OTARM_DATABASE_URL = "postgresql+psycopg://otarm:password@localhost:5432/otarm"
uv run python -m uvicorn app.main:app --reload --port 8000
```

The repository root also contains `docker-compose.yaml`, which starts PostgreSQL and the full application together:

```powershell
$env:POSTGRES_PASSWORD = "choose-a-database-password"
$env:OTARM_DEMO_PASSWORD = "choose-a-demo-password"
$env:OTARM_TOKEN_SECRET = "choose-a-long-random-token-secret"
docker compose up --build
```

PostgreSQL uses `POSTGRES_PASSWORD` only when it initializes an empty data
volume. Changing that environment variable later does not change the password
stored for the existing `otarm` role. If the database contains data you need to
keep, update the role interactively and then restart the application:

```powershell
docker compose exec db psql -U otarm -d otarm
```

At the `psql` prompt, run `\password otarm`, enter the same value currently set
in `POSTGRES_PASSWORD` twice, and exit with `\q`. Then run:

```powershell
docker compose restart app
```

For disposable development data, `docker compose down -v` removes the database
volume so the next `docker compose up --build` initializes it with the current
password. That command permanently deletes the Compose-managed PostgreSQL data.

Tables and fictional seed data are created when the configured database is empty. On each startup, an explicitly configured `OTARM_DEMO_PASSWORD` updates the four fictional `@otarm.demo` accounts without altering inventory or risk records, allowing predictable local password rotation.

Seeded fictional users are `assessor@otarm.demo`, `approver@otarm.demo`, `viewer@otarm.demo`, and `admin@otarm.demo`. All use the password supplied in `OTARM_DEMO_PASSWORD`.

Obtain a bearer token from `POST /api/v1/auth/token`, then pass it as `Authorization: Bearer <token>`. Tokens expire after 60 minutes by default. Configure `OTARM_TOKEN_TTL_SECONDS` or supply `OTARM_TOKEN_SECRET` for a stable development signing secret. Production deployments must use a secret manager and durable identity provider.

## OpenTelemetry

Every HTTP request is traced with OpenTelemetry. Spans carry `service.name`,
`deployment.environment.name`, and `service.version` resource attributes. Configure
them with `OTEL_SERVICE_NAME` (default `otarm-backend`), `OTARM_ENVIRONMENT`
(default `development`), and `OTARM_VERSION` (default package version; on Render,
`RENDER_GIT_COMMIT` is used when present).

Set `OTEL_EXPORTER_OTLP_ENDPOINT` (or the trace-specific
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`) to send traces to an OTLP/HTTP collector.
Standard OpenTelemetry exporter variables such as `OTEL_EXPORTER_OTLP_HEADERS`
are also supported. When no endpoint is set, requests remain instrumented but no
exporter is installed, so local development does not attempt an external connection.

When the general endpoint or `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` is set, the
backend also exports these low-cardinality application metrics:

- `otarm_http_server_requests_total`
- `otarm_http_server_request_duration_seconds`
- `otarm_http_server_active_requests`
- `otarm_http_server_errors_total`
- `otarm_db_operation_duration_seconds`
- `otarm_db_operation_errors_total`
- `otarm_auth_attempts_total`
- `otarm_authorization_denials_total`
- `otarm_audit_events_total`
- `otarm_risk_assessments_total`

Metrics carry the same `service.name`, `deployment.environment.name`, and
`service.version` resource attributes as traces. HTTP labels use route templates,
database labels contain only the backend and operation, and no asset identifiers,
user identifiers, email addresses, stored IP addresses, or SQL statements are
recorded. `OTEL_METRIC_EXPORT_INTERVAL` controls the export interval in
milliseconds and defaults to `60000`.

## Tests

```powershell
cd backend
uv run pytest
```

The default command runs the fast backend suite and excludes Docker integration
tests. To build and exercise an isolated `docker-compose.yaml` stack against a
temporary PostgreSQL volume, run:

```powershell
uv run python -m pytest -m integration
```

The integration suite requires a running Docker Desktop. It verifies frontend
delivery, API routing, authentication, authorization, PostgreSQL writes,
duplicate constraints, audit events, persistence after an app restart,
dashboard calculations, and remediation separation of duties. Its Compose
project and database volume are removed in teardown.

The backend stores OT IP addresses as display-only strings. It contains no discovery, scanning, protocol polling, patching, or device-connection code. Automatic `create_all` setup is suitable for this development MVP. Production deployments still require versioned migrations, managed credentials, backups, connection monitoring, and externally immutable audit retention.
