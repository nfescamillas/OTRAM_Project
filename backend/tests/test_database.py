from pathlib import Path

from app.auth import verify_password
from app.database import create_database_engine, normalize_database_url
from app.main import create_app
from app.models import AssetInput, AssetType, Criticality, LifecycleState, OperationalStatus, VerificationState
from app.store import DatabaseStore


def test_sqlite_store_persists_records_across_instances(tmp_path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'persistent.db').as_posix()}"
    first = DatabaseStore(database_url, "first-password", password_iterations=1_000)
    user = first.user_by_email("assessor@otarm.demo")
    assert user is not None
    first.create_asset(user, AssetInput(
        tag="PERSIST-PLC-001", name="Persistent PLC", type=AssetType.PLC, siteId="site-north",
        area="Utilities", vendor="Fictional Controls", model="FC-1", criticality=Criticality.HIGH,
        lifecycle=LifecycleState.UNKNOWN, verification=VerificationState.UNVERIFIED,
        operationalStatus=OperationalStatus.ACTIVE,
    ))
    first.dispose()

    second = DatabaseStore(database_url, "second-password", password_iterations=1_000)
    same_user = second.user_by_email("assessor@otarm.demo")
    assert same_user is not None
    assert [asset.tag for asset in second.list_assets(same_user, search="PERSIST-PLC-001")] == ["PERSIST-PLC-001"]
    second.dispose()


def test_create_app_uses_database_url_from_environment(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "configured.db"
    monkeypatch.setenv("OTARM_DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    monkeypatch.setenv("OTARM_DEMO_PASSWORD", "environment-password")

    app = create_app()

    assert database_path.exists()
    assert Path(app.state.store.engine.url.database).resolve() == database_path.resolve()
    user = app.state.store.user_by_email("admin@otarm.demo")
    assert user is not None
    assert verify_password("environment-password", user.passwordHash)
    app.state.store.dispose()


def test_postgresql_urls_use_psycopg_3_driver() -> None:
    assert normalize_database_url(
        "postgresql://otarm:secret@db:5432/otarm"
    ) == "postgresql+psycopg://otarm:secret@db:5432/otarm"
    assert normalize_database_url(
        "postgres://otarm:secret@db:5432/otarm"
    ) == "postgresql+psycopg://otarm:secret@db:5432/otarm"

    engine = create_database_engine("postgresql://otarm:secret@db:5432/otarm")

    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.pool._pre_ping is True
    engine.dispose()
