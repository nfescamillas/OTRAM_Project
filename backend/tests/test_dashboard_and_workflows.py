from collections.abc import Callable

from fastapi.testclient import TestClient


def test_dashboard_matches_seeded_records(client: TestClient, auth_headers: Callable) -> None:
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["activeAssets"] == 8
    assert body["assessedAssets"] == 5
    assert body["coveragePercent"] == 63
    assert body["severityCounts"] == {"LOW": 0, "MEDIUM": 0, "HIGH": 3, "CRITICAL": 1}
    assert body["topPriorities"][0]["id"] == "f1"


def test_site_filter_applies_to_dashboard_and_findings(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers()
    dashboard = client.get("/api/v1/dashboard/summary", params={"siteId": "site-water"}, headers=headers)
    assert dashboard.json()["activeAssets"] == 3
    findings = client.get("/api/v1/findings", params={"siteId": "site-water", "severity": "HIGH"}, headers=headers)
    assert [item["id"] for item in findings.json()] == ["f2"]


def test_remediation_transition_and_audit(client: TestClient, auth_headers: Callable) -> None:
    assessor = auth_headers("assessor")
    changed = client.patch("/api/v1/actions/r3/status", json={"status": "PLANNED"}, headers=assessor)
    assert changed.status_code == 200
    assert changed.json()["status"] == "PLANNED"
    audit = client.get("/api/v1/audit-events", headers=auth_headers("approver"))
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "ACTION_STATUS_CHANGED"


def test_assessor_cannot_verify_but_approver_can(client: TestClient, auth_headers: Callable) -> None:
    assessor = client.patch("/api/v1/actions/r1/status", json={"status": "VERIFIED"}, headers=auth_headers("assessor"))
    assert assessor.status_code == 403
    approved = client.patch("/api/v1/actions/r1/status", json={"status": "VERIFIED"}, headers=auth_headers("approver"))
    assert approved.status_code == 200
    assert approved.json()["status"] == "VERIFIED"


def test_viewer_cannot_change_actions_or_read_audit(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers("viewer")
    assert client.patch("/api/v1/actions/r3/status", json={"status": "PLANNED"}, headers=headers).status_code == 403
    assert client.get("/api/v1/audit-events", headers=headers).status_code == 403


def test_invalid_transition_is_conflict(client: TestClient, auth_headers: Callable) -> None:
    response = client.patch("/api/v1/actions/r3/status", json={"status": "VERIFIED"}, headers=auth_headers("approver"))
    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"
