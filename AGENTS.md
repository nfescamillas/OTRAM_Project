# OTARM coding-agent instructions

## Repository boundaries

- `frontend/` owns the React/Vite client, its mock service, browser-side domain helpers, styling, and frontend tests.
- `backend/` owns the authenticated FastAPI application, SQLAlchemy persistence, future migrations, and backend tests.
- `_docs/` contains the approved product and design baselines. Preserve their requirements unless the user explicitly changes them.
- `openapi.yaml` is the frontend/backend API agreement. Update it with intentional API changes before changing both sides independently.

## Required architectural rules

1. Route every frontend data operation through `frontend/src/services/otarmService.ts`. Components must not call `fetch`, import mock seed records, or access persistence directly.
2. Keep the mock implementation runnable without a backend. A future HTTP implementation must satisfy the same service interface.
3. Never add active or passive OT discovery, protocol polling, device probing, automatic patching, or requests to stored asset IP addresses.
4. Treat lifecycle, firmware, and support assertions as human-provided evidence. Never infer lifecycle state from a vendor or model name.
5. Calculate risk as impact × likelihood through the domain function. Do not trust client-submitted scores.
6. Preserve organization scope, separation of duties, immutable assessment history, and append-only audit behavior when implementing the backend.
7. Use fictional data only. Do not commit credentials, private plant inventories, tokens, or database dumps.

## Frontend workflow

Run frontend commands from `frontend/`:

```bash
npm run typecheck
npm test
npm run build
```

Maintain the graphite industrial design language from `_docs/design.md`: compact information density, restrained semantic colors, squared technical components, accessible focus states, and monospaced technical values.

## Backend workflow

The backend is a FastAPI application managed with `uv`. Run backend commands from `backend/`:

```bash
uv sync --dev
uv run pytest
```

Keep routers, models, the in-memory store, and authentication separated under `backend/app/`. Verify route and operation parity against `openapi.yaml`. Do not imply that the in-memory store provides production durability or audit immutability; a database-backed implementation remains required for production.
