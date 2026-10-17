from fastapi.testclient import TestClient

from app.auth import TokenService, hash_password, verify_password
from app.models import Role, UserRecord


def test_passwords_are_salted_and_verified() -> None:
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert first.startswith("pbkdf2_sha256$")
    assert "correct horse" not in first
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong", first)


def test_token_round_trip_and_tamper_rejection() -> None:
    service = TokenService(b"a-signing-secret-that-is-at-least-32-bytes")
    user = UserRecord(id="u1", email="user@example.test", displayName="User", role=Role.VIEWER,
                      organizationId="org1", passwordHash="unused")
    token = service.issue(user)
    assert service.verify(token)["sub"] == "u1"
    try:
        service.verify(token + "tampered")
        raise AssertionError("Tampered token was accepted")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 401


def test_login_returns_bearer_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/token", json={
        "email": "assessor@otarm.demo", "password": "test-only-password"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] == 3600
    assert body["user"]["role"] == "ASSESSOR"
    assert body["accessToken"]


def test_login_rejects_bad_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/token", json={
        "email": "assessor@otarm.demo", "password": "wrong"
    })
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_every_business_endpoint_requires_authentication(client: TestClient) -> None:
    requests = [
        ("GET", "/api/v1/sites"),
        ("GET", "/api/v1/dashboard/summary"),
        ("GET", "/api/v1/assets"),
        ("GET", "/api/v1/assets/a1"),
        ("GET", "/api/v1/assets/export.csv"),
        ("GET", "/api/v1/findings"),
        ("GET", "/api/v1/remediation"),
        ("PATCH", "/api/v1/actions/r3/status"),
        ("GET", "/api/v1/audit-events"),
    ]
    for method, path in requests:
        response = client.request(method, path, json={"status": "PLANNED"} if method == "PATCH" else None)
        assert response.status_code == 401, path
        assert response.json()["code"] == "UNAUTHENTICATED"
