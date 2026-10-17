from __future__ import annotations

import os
import secrets
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest


pytestmark = pytest.mark.integration

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPOSITORY_ROOT / "docker-compose.yaml"


@dataclass(frozen=True)
class ComposeStack:
    base_url: str
    demo_password: str
    environment: dict[str, str]
    project_name: str

    def compose(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "docker", "compose", "--project-name", self.project_name,
                "--file", str(COMPOSE_FILE), *arguments,
            ],
            cwd=REPOSITORY_ROOT,
            env=self.environment,
            check=check,
            capture_output=True,
            text=True,
            timeout=600,
        )

    def wait_until_ready(self, timeout_seconds: int = 90) -> None:
        deadline = time.monotonic() + timeout_seconds
        with httpx.Client(base_url=self.base_url, timeout=2) as client:
            while time.monotonic() < deadline:
                try:
                    if client.get("/").status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                time.sleep(1)
        logs = self.compose("logs", "--no-color", check=False)
        pytest.fail(f"Compose application did not become ready.\n{logs.stdout}\n{logs.stderr}")

    def login(self, role: str) -> dict[str, str]:
        response = httpx.post(
            f"{self.base_url}/api/v1/auth/token",
            json={"email": f"{role}@otarm.demo", "password": self.demo_password},
            timeout=10,
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def _available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@pytest.fixture()
def compose_stack() -> Iterator[ComposeStack]:
    if shutil.which("docker") is None:
        pytest.fail("Docker is required for Compose integration tests.")
    daemon = subprocess.run(
        ["docker", "info"], capture_output=True, text=True, check=False, timeout=30
    )
    if daemon.returncode != 0:
        pytest.fail(f"Docker is not available. Start Docker Desktop first.\n{daemon.stderr}")

    port = _available_port()
    environment = os.environ.copy()
    environment.update({
        "POSTGRES_PASSWORD": f"postgres-{secrets.token_hex(16)}",
        "OTARM_DEMO_PASSWORD": f"demo-{secrets.token_hex(16)}",
        "OTARM_TOKEN_SECRET": secrets.token_hex(48),
        "OTARM_PORT": str(port),
    })
    stack = ComposeStack(
        base_url=f"http://127.0.0.1:{port}",
        demo_password=environment["OTARM_DEMO_PASSWORD"],
        environment=environment,
        project_name=f"otarm-integration-{secrets.token_hex(4)}",
    )

    try:
        started = stack.compose("up", "--build", "--detach", check=False)
        if started.returncode != 0:
            pytest.fail(f"Could not start Compose stack.\n{started.stdout}\n{started.stderr}")
        stack.wait_until_ready()
        yield stack
    finally:
        stack.compose("down", "--volumes", "--remove-orphans", check=False)


def test_frontend_and_api_are_served_by_the_built_app(compose_stack: ComposeStack) -> None:
    with httpx.Client(base_url=compose_stack.base_url, timeout=10) as client:
        frontend = client.get("/")
        openapi = client.get("/openapi.json")

    assert frontend.status_code == 200
    assert '<div id="root"></div>' in frontend.text
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "OTARM Frontend Backend API"


def test_authentication_and_protected_routes(compose_stack: ComposeStack) -> None:
    invalid = httpx.post(
        f"{compose_stack.base_url}/api/v1/auth/token",
        json={"email": "assessor@otarm.demo", "password": "incorrect"},
        timeout=10,
    )
    anonymous = httpx.get(f"{compose_stack.base_url}/api/v1/assets", timeout=10)
    headers = compose_stack.login("assessor")
    authenticated = httpx.get(
        f"{compose_stack.base_url}/api/v1/assets", headers=headers, timeout=10
    )

    assert invalid.status_code == 401
    assert invalid.json()["code"] == "UNAUTHENTICATED"
    assert anonymous.status_code == 401
    assert authenticated.status_code == 200
    assert len(authenticated.json()) == 8


def test_postgres_write_authorization_audit_and_restart_persistence(
    compose_stack: ComposeStack,
) -> None:
    payload = {
        "tag": "IT-PLC-001",
        "name": "Integration Test PLC",
        "type": "PLC",
        "siteId": "site-north",
        "area": "Test Cell",
        "vendor": "Fictional Controls",
        "model": "IT-100",
        "criticality": "HIGH",
        "lifecycle": "UNKNOWN",
        "verification": "UNVERIFIED",
        "operationalStatus": "ACTIVE",
    }
    viewer = compose_stack.login("viewer")
    assessor = compose_stack.login("assessor")

    forbidden = httpx.post(
        f"{compose_stack.base_url}/api/v1/assets", json=payload, headers=viewer, timeout=10
    )
    created = httpx.post(
        f"{compose_stack.base_url}/api/v1/assets", json=payload, headers=assessor, timeout=10
    )
    duplicate = httpx.post(
        f"{compose_stack.base_url}/api/v1/assets", json=payload, headers=assessor, timeout=10
    )

    assert forbidden.status_code == 403
    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "CONFLICT"

    compose_stack.compose("restart", "app")
    compose_stack.wait_until_ready()
    persisted = httpx.get(
        f"{compose_stack.base_url}/api/v1/assets",
        params={"search": payload["tag"]},
        headers=compose_stack.login("assessor"),
        timeout=10,
    )
    audit = httpx.get(
        f"{compose_stack.base_url}/api/v1/audit-events",
        headers=compose_stack.login("approver"),
        timeout=10,
    )

    assert persisted.status_code == 200
    assert [asset["tag"] for asset in persisted.json()] == [payload["tag"]]
    assert any(
        event["action"] == "ASSET_CREATED" and event["entity"] == payload["tag"]
        for event in audit.json()
    )


def test_seeded_dashboard_and_remediation_separation_of_duties(
    compose_stack: ComposeStack,
) -> None:
    assessor = compose_stack.login("assessor")
    approver = compose_stack.login("approver")
    dashboard = httpx.get(
        f"{compose_stack.base_url}/api/v1/dashboard/summary", headers=assessor, timeout=10
    )
    assessor_verification = httpx.patch(
        f"{compose_stack.base_url}/api/v1/actions/r1/status",
        json={"status": "VERIFIED"},
        headers=assessor,
        timeout=10,
    )
    approver_verification = httpx.patch(
        f"{compose_stack.base_url}/api/v1/actions/r1/status",
        json={"status": "VERIFIED"},
        headers=approver,
        timeout=10,
    )

    assert dashboard.status_code == 200
    assert dashboard.json()["activeAssets"] == 8
    assert dashboard.json()["severityCounts"] == {
        "LOW": 0, "MEDIUM": 0, "HIGH": 3, "CRITICAL": 1,
    }
    assert assessor_verification.status_code == 403
    assert approver_verification.status_code == 200
    assert approver_verification.json()["status"] == "VERIFIED"
