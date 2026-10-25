from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_AGENT_COMMAND = (
    "codex",
    "exec",
    "--ephemeral",
    "--ignore-user-config",
    "--sandbox",
    "read-only",
    "--color",
    "never",
    "-",
)


def _positive_number(name: str, default: str, *, integer: bool = False) -> float | int:
    raw = os.getenv(name, default)
    try:
        value = int(raw) if integer else float(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive number") from error
    if value <= 0:
        raise ValueError(f"{name} must be a positive number")
    return value


def _path_from(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


@dataclass(frozen=True)
class Config:
    alerts_url: str
    alerts_token: str | None
    repository: Path
    poll_seconds: float
    request_timeout_seconds: float
    agent_timeout_seconds: int
    max_concurrent_agents: int
    state_file: Path
    runs_directory: Path
    agent_command: tuple[str, ...]

    @classmethod
    def from_environment(cls, base_directory: Path | None = None) -> "Config":
        base = (base_directory or Path.cwd()).resolve()
        alerts_url = os.getenv(
            "ON_CALL_ALERTS_URL", "http://localhost:9090/api/v1/alerts"
        ).strip()
        parsed_url = urlsplit(alerts_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("ON_CALL_ALERTS_URL must be an http(s) URL")
        if parsed_url.username or parsed_url.password:
            raise ValueError("Put credentials in ON_CALL_ALERTS_TOKEN, not in the URL")

        command_raw = os.getenv("ON_CALL_AGENT_COMMAND")
        if command_raw:
            try:
                command_value = json.loads(command_raw)
            except json.JSONDecodeError as error:
                raise ValueError("ON_CALL_AGENT_COMMAND must be a JSON array") from error
            if not isinstance(command_value, list) or not command_value or not all(
                isinstance(part, str) and part for part in command_value
            ):
                raise ValueError("ON_CALL_AGENT_COMMAND must be a non-empty JSON string array")
            command = tuple(command_value)
        else:
            command = DEFAULT_AGENT_COMMAND

        repository = _path_from(base, os.getenv("ON_CALL_REPOSITORY", ".."))
        if not repository.is_dir():
            raise ValueError(f"ON_CALL_REPOSITORY is not a directory: {repository}")

        return cls(
            alerts_url=alerts_url,
            alerts_token=os.getenv("ON_CALL_ALERTS_TOKEN") or None,
            repository=repository,
            poll_seconds=float(_positive_number("ON_CALL_POLL_SECONDS", "60")),
            request_timeout_seconds=float(
                _positive_number("ON_CALL_REQUEST_TIMEOUT_SECONDS", "10")
            ),
            agent_timeout_seconds=int(
                _positive_number("ON_CALL_AGENT_TIMEOUT_SECONDS", "900", integer=True)
            ),
            max_concurrent_agents=int(
                _positive_number("ON_CALL_MAX_CONCURRENT_AGENTS", "2", integer=True)
            ),
            state_file=_path_from(base, os.getenv("ON_CALL_STATE_FILE", "var/state.json")),
            runs_directory=_path_from(
                base, os.getenv("ON_CALL_RUNS_DIRECTORY", "var/runs")
            ),
            agent_command=command,
        )
