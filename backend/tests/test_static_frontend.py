from fastapi.testclient import TestClient

from app.auth import TokenService
from app.main import create_app
from app.store import DatabaseStore


def test_backend_serves_built_frontend(tmp_path) -> None:
    static_dir = tmp_path / "static"
    assets_dir = static_dir / "assets"
    assets_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text("<h1>OTARM</h1>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('otarm')", encoding="utf-8")

    app = create_app(
        store=DatabaseStore("sqlite:///:memory:", "test-password", password_iterations=1_000),
        token_service=TokenService(b"test-signing-secret-that-is-long-enough-123456", ttl_seconds=3600),
        static_dir=static_dir,
    )

    with TestClient(app) as client:
        index_response = client.get("/")
        asset_response = client.get("/assets/app.js")

    assert index_response.status_code == 200
    assert "OTARM" in index_response.text
    assert asset_response.status_code == 200
    assert asset_response.text == "console.log('otarm')"
