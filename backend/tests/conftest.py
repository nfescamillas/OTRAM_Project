import os
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("OTARM_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OTARM_DEMO_PASSWORD", "test-global-password")

from app.auth import TokenService
from app.main import create_app
from app.store import DatabaseStore


TEST_PASSWORD = "test-only-password"


@pytest.fixture()
def client(tmp_path) -> TestClient:
    database_url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    app = create_app(
        store=DatabaseStore(database_url, TEST_PASSWORD, password_iterations=1_000),
        token_service=TokenService(b"test-signing-secret-that-is-long-enough-123456", ttl_seconds=3600),
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient) -> Callable[[str], dict[str, str]]:
    def login(role: str = "assessor") -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/token",
            json={"email": f"{role}@otarm.demo", "password": TEST_PASSWORD},
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['accessToken']}"}

    return login
