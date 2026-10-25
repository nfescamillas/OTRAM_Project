# OTARM on-call engineer

This worker polls the Prometheus alerts API once per minute and starts one
bounded, headless Codex triage run for each alert when it first enters the
`firing` state. It is deliberately separate from the OTARM backend and does not
change the frontend/backend API contract.

The default agent is **read-only**. It may inspect this repository and propose a
response, but it cannot edit files. The prompt also prohibits deployment,
rollback, external-system writes, and any contact with stored OT asset IP
addresses. Alert labels and annotations are treated as untrusted input.

## Run

Requirements: Python 3.12+, `uv`, an authenticated `codex` CLI, and a reachable
Prometheus API.

```powershell
Set-Location on-call-engineer
Copy-Item .env.example .env
# Load the ON_CALL_* values using your process supervisor or shell.
uv sync --dev
uv run otarm-on-call --once
uv run otarm-on-call
```

Prometheus in the current observability Compose stack is intentionally not
published to the host. For a host process, either expose it through an
authenticated reverse proxy or run this worker on the
`otarm-observability-internal` Docker network and use
`http://prometheus:9090/api/v1/alerts`. Do not publish an unauthenticated
Prometheus endpoint to a public interface.

Configuration is entirely through environment variables; see `.env.example`.
`ON_CALL_AGENT_COMMAND` is a JSON array, not a shell command. Keeping it as an
argument vector prevents alert content from becoming shell syntax.

## Delivery semantics

- Only alerts whose Prometheus state is exactly `firing` are dispatched.
- The label set is hashed when the API supplies no fingerprint.
- Active fingerprints are persisted atomically in `var/state.json`.
- A continuously firing alert is dispatched once. After it resolves, a later
  firing transition is dispatched again.
- State is recorded before agent launch, providing at-most-once delivery. A
  failed or timed-out run is not automatically retried; inspect the JSON result
  in `var/runs/` and retry explicitly to avoid an agent retry storm.
- Each run is bounded by `ON_CALL_AGENT_TIMEOUT_SECONDS` (15 minutes by default).
- Polling continues while triage runs execute. A bounded worker pool limits agent
  concurrency (`ON_CALL_MAX_CONCURRENT_AGENTS`, two by default).

## Production hardening

Run the process under a supervisor (systemd, Kubernetes, or a container
platform), send its structured result artifacts to durable restricted storage,
and alert on worker health. Use a dedicated machine identity and a narrowly
scoped repository checkout. If you later allow edits, prefer a disposable Git
worktree and require a human-reviewed pull request; do not grant deployment or
production credentials to the agent process.

Run tests with:

```powershell
uv run pytest
```
