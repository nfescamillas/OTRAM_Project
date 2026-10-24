# OTARM — OT Asset & Risk Manager

[![CI](https://github.com/nfescamillas/OTRAM_Project/actions/workflows/ci.yml/badge.svg)](https://github.com/nfescamillas/OTRAM_Project/actions/workflows/ci.yml)

A frontend implementation of the approved [`_docs/plan.md`](./_docs/plan.md) baseline. It provides an interactive OT inventory, risk dashboard, risk register, remediation workflow, exports, and audit view using clearly fictional demo data.

## Repository layout

```text
backend/     FastAPI application, SQLAlchemy persistence, authentication, and tests
_docs/       Product requirements and interface design guidance
frontend/    Vite/React application, browser mock service, and frontend tests
AGENTS.md    Repository instructions for coding agents
openapi.yaml Versioned frontend/backend API agreement
```

## Run locally

With GNU Make installed, the shortest path is:

```bash
make install
make dev DEMO_PASSWORD="choose-a-local-demo-password"
```

This starts the frontend on port `5173` and the backend on port `8000`. Sign in as `admin@otarm.demo` (or another seeded `@otarm.demo` user) with the password passed to `make dev`. Run `make help` for individual service, test, type-check, and build targets.

Without Make:

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite URL shown in the terminal.

## Development environment with Docker Compose

Docker Compose is the recommended way to run the complete application. It starts
PostgreSQL and builds the application image, including the React frontend and
FastAPI backend.

From the repository root, set the required values in PowerShell:

```powershell
$env:POSTGRES_PASSWORD = "choose-a-database-password"
$env:OTARM_DEMO_PASSWORD = "choose-a-demo-password"
$env:OTARM_TOKEN_SECRET = "choose-a-long-random-token-secret"
```

Use strong, unique values outside local development. Keep these variables set in
the same PowerShell session used for subsequent Compose commands. If you open a
new PowerShell session, set them again before running any `docker compose`
command, including the stop commands below.

Build and start both services in the background:

```powershell
docker compose up --build -d
```

Compose waits for PostgreSQL to become healthy before starting the application.
Check service status or follow application logs with:

```powershell
docker compose ps
docker compose logs -f app
```

Open `http://localhost:8000` and sign in as `admin@otarm.demo` using the value
set in `OTARM_DEMO_PASSWORD`. If port `8000` is already occupied, set another
host port before starting the services:

```powershell
$env:OTARM_PORT = "18000"
docker compose up --build -d
```

The application will then be available at `http://localhost:18000`.

### Stop the application

Stop and remove the application and database containers and their network:

```powershell
docker compose down
```

This preserves the `postgres-data` named volume. Running `docker compose up -d`
later starts the application again with the existing database contents.

To stop the containers without removing them, use:

```powershell
docker compose stop
```

Resume those stopped containers with:

```powershell
docker compose start
```

To remove the containers **and permanently delete all PostgreSQL data**, use:

```powershell
docker compose down -v
```

Do not use `-v` when the database contains information you need to retain.

## Independent production copy

The existing `docker-compose.yaml` remains the development environment. A
second definition, `docker-compose.production.yaml`, runs an independent stack
under the fixed `otarm-production` Compose project name. It has its own
PostgreSQL database, volume, internal network, credentials, containers, and
host port. Starting, stopping, or recreating it does not operate on the
development stack.

Copy the committed template and replace every placeholder with production-only
values:

```powershell
Copy-Item .env.production.example .env.production
```

Use a long hexadecimal (or otherwise URL-encoded) database password because
the application receives it inside a PostgreSQL connection URL. The production
environment file is excluded from both Git and Docker build contexts.

Set `OTARM_IMAGE` to the immutable `sha-<full-commit-sha>` tag published by a
successful `main` build. Do not deploy the mutable `main` tag. Validate and
start the production copy with:

```powershell
docker compose --env-file .env.production -f docker-compose.production.yaml config --quiet
docker compose --env-file .env.production -f docker-compose.production.yaml pull
docker compose --env-file .env.production -f docker-compose.production.yaml up -d
docker compose --env-file .env.production -f docker-compose.production.yaml ps
```

The production copy listens on `http://localhost:8080` by default; change
`OTARM_PROD_PORT` in `.env.production` if needed. Development continues to use
`http://localhost:8000`, and both copies can run at the same time.

Operate each stack with its own Compose file:

```powershell
# Production logs/restart/stop
docker compose --env-file .env.production -f docker-compose.production.yaml logs -f app
docker compose --env-file .env.production -f docker-compose.production.yaml restart app
docker compose --env-file .env.production -f docker-compose.production.yaml down

# Development status/stop
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml down
```

`down` preserves each environment's database volume. Never run `down -v` for
the production copy unless permanent deletion of the production database is
explicitly intended and a tested backup exists. The production database volume
is named in the `otarm-production` namespace and is never shared with dev.

This provides deployment isolation, but it does not remove the MVP limitations:
production use still requires scheduled and tested backups, versioned database
migrations, managed secret storage and identity, monitoring, TLS/reverse-proxy
termination, and externally immutable audit retention. The included PostgreSQL
container is persistent, not a substitute for a managed high-availability
database.

## Deploy on Render

The root [`render.yaml`](./render.yaml) deploys the application as one Docker web
service and provisions a Render Postgres database. The React build is served by
FastAPI, so the browser and API share one origin and no public CORS configuration
is required. The database accepts private-network connections only.

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. In the Render Dashboard, select **New > Blueprint** and connect the repository.
3. Keep `render.yaml` as the Blueprint path and review the two proposed resources.
4. Enter a strong value for `OTARM_DEMO_PASSWORD` when Render prompts for it.
   Render generates `OTARM_TOKEN_SECRET` and wires `OTARM_DATABASE_URL` to the
   managed database automatically.
5. Apply the Blueprint and wait for `/healthz` to report healthy.
6. Open the web service URL and sign in as `admin@otarm.demo` with the demo
   password you entered. The other seeded roles use `assessor@otarm.demo`,
   `approver@otarm.demo`, and `viewer@otarm.demo` with that same password.

The committed Blueprint uses Render's free web-service and PostgreSQL plans for
evaluation. Free web services can spin down while idle, and free Render Postgres
databases expire 30 days after creation and have no backups. Before storing data
that must survive, upgrade both resources to appropriate paid plans and establish
tested backups. This MVP also creates tables directly at startup; add versioned
database migrations before using rolling schema changes in production.

Render builds the root Dockerfile and the container binds to Render's `PORT`
value, falling back to port `8000` for local Docker use. Automatic deploys wait
for the linked repository's checks to pass.

## Quality checks

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

The regular backend suite excludes Docker integration tests. To build an
isolated Compose project, test it against a temporary PostgreSQL volume, and
remove the test stack afterward, run:

```powershell
cd backend
uv run python -m pytest -m integration
```

Docker Desktop must be running. The integration suite chooses a free host port
and generates its own test credentials, so it does not use or remove the normal
development stack or its `postgres-data` volume. With GNU Make, the equivalent
command is `make test-integration` from the repository root.

## CI/CD

GitHub Actions validates every pull request to `main` and every push to `main`.
The workflow runs frontend and backend checks in parallel. After both pass, it
builds one isolated Docker Compose stack and exercises that running application
with API/PostgreSQL integration tests and a Playwright browser end-to-end test.

After all checks pass on a push to `main`, the workflow builds the application
image once more with BuildKit and publishes it to GitHub Container Registry as:

```text
ghcr.io/nfescamillas/otram_project:sha-<full-commit-sha>
ghcr.io/nfescamillas/otram_project:main
```

The immutable SHA tag is the deployment artifact. Future staging and production
workflows should promote that exact image rather than rebuild it. The image is
published with an SBOM and provenance metadata. CI uses only ephemeral test
credentials generated by the integration suite; no AWS credentials are needed.

### Promote a tested image to production

The `Promote dev image to production` workflow is manual. In the repository's
Actions tab, select that workflow, choose **Run workflow**, and enter the full
immutable tag produced by CI, such as `sha-0123456789abcdef0123456789abcdef01234567`.
The workflow rejects mutable tags and abbreviated SHAs. It does not rebuild the
application: it verifies that the selected image exists, points the registry's
`production` tag at the same manifest, and verifies that the digest did not
change.

The promotion job uses the GitHub `production` environment. Configure that
environment in repository settings with required reviewers so a manual dispatch
also requires an explicit production approval. The workflow needs only the
repository-provided `GITHUB_TOKEN`, with package-write permission; it does not
consume application or database secrets.

After promotion, keep `OTARM_IMAGE` in `.env.production` pinned to the selected
immutable `sha-...` tag (or its reported digest), then run the production pull
and `up -d` commands above. The mutable `production` tag is an auditable
promotion pointer, not the deployment pin.

Weekly Dependabot checks cover npm, uv, the Dockerfile, Docker Compose, and
GitHub Actions dependencies.

## Architecture

All UI data access is routed through `frontend/src/services/otarmService.ts`. The app binds that contract to `HttpOtarmService`, which authenticates against and calls the FastAPI implementation of `openapi.yaml`. During local development, Vite proxies `/api/v1` to `http://127.0.0.1:8000`; deployments can set `VITE_OTARM_API_BASE_URL` at build time. Bearer sessions are held in browser session storage and cleared on expiry or an unauthorized response. UI components never call `fetch` or access persistence directly.

`MockOtarmService` remains available for isolated frontend testing and backend-free development. It implements:

- Site-scoped dashboard metrics and deterministic priority sorting.
- Search and filters for assets and findings.
- Asset creation with duplicate-tag validation and audit events.
- Remediation state updates.
- Organization-style scoped CSV export with formula-injection neutralization.
- Detached return values to prevent callers mutating service state.

The risk domain module implements the plan's OTARM-5X5 v1 arithmetic and boundary policy. Tests cover scoring boundaries, prioritization, CSV safety, service filtering, isolation, dashboard counts, exports, and the application shell.

The FastAPI backend under `backend/` implements the root `openapi.yaml` contract with SQLAlchemy, PostgreSQL or SQLite persistence, PBKDF2 password hashes, expiring bearer tokens, organization-scoped data access, role checks, remediation transition validation, and API contract tests. Configure the database with `OTARM_DATABASE_URL`; see `backend/README.md` for setup and runtime details.

## Safety boundary

This implementation never probes, scans, polls, writes to, configures, or patches OT equipment. Stored IP addresses are display-only. Lifecycle and support states are treated as human-provided evidence, never inferred from model names.

## Demo limitations

This remains a development MVP: SQLite and PostgreSQL provide development persistence, while production identity, managed PostgreSQL operations, versioned migrations, backups, concurrent deployment controls, imports, and externally immutable audit retention remain future work.
