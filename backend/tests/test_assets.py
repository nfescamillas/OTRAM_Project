from collections.abc import Callable

from fastapi.testclient import TestClient


def new_asset(tag: str = "NPR-PLC-099") -> dict:
    return {
        "tag": tag, "name": "Condensate Transfer PLC", "type": "PLC", "siteId": "site-north",
        "area": "Utilities", "vendor": "Rockwell Automation", "model": "ControlLogix 5580",
        "criticality": "HIGH", "lifecycle": "UNKNOWN", "verification": "UNVERIFIED",
        "operationalStatus": "ACTIVE", "owner": "Maya Chen", "firmware": "v35.011",
        "networkZone": "Cell 2 - Utilities", "ipAddress": "10.42.20.99"
    }


def test_seeded_assets_and_filters(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers()
    response = client.get("/api/v1/assets", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 8
    filtered = client.get("/api/v1/assets", params={"siteId": "site-water", "type": "PLC", "search": "chemical"}, headers=headers)
    assert [item["tag"] for item in filtered.json()] == ["WTP-PLC-021"]


def test_get_asset_and_not_found(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers()
    assert client.get("/api/v1/assets/a1", headers=headers).json()["name"] == "Boiler Feedwater PLC"
    missing = client.get("/api/v1/assets/missing", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == "NOT_FOUND"


def test_assessor_creates_asset_and_duplicate_is_atomic(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers("assessor")
    created = client.post("/api/v1/assets", json=new_asset(), headers=headers)
    assert created.status_code == 201
    assert created.json()["assessed"] is False
    duplicate = client.post("/api/v1/assets", json=new_asset(), headers=headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "CONFLICT"
    matches = client.get("/api/v1/assets", params={"search": "NPR-PLC-099"}, headers=headers).json()
    assert len(matches) == 1


def test_viewer_cannot_create_or_export(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers("viewer")
    assert client.post("/api/v1/assets", json=new_asset(), headers=headers).status_code == 403
    assert client.get("/api/v1/assets/export.csv", headers=headers).status_code == 403


def test_csv_export_honors_filters_and_neutralizes_formulas(client: TestClient, auth_headers: Callable) -> None:
    headers = auth_headers("assessor")
    assert client.post("/api/v1/assets", json=new_asset("=1+1"), headers=headers).status_code == 201
    response = client.get("/api/v1/assets/export.csv", params={"search": "=1+1"}, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "'=1+1" in response.text
    assert "NPR-PLC-014" not in response.text


def test_validation_errors_use_agreed_shape(client: TestClient, auth_headers: Callable) -> None:
    response = client.post("/api/v1/assets", json={"tag": "incomplete"}, headers=auth_headers())
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION"
    assert response.json()["fields"]
