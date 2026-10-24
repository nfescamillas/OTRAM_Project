from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_render_blueprint_wires_web_service_to_private_database() -> None:
    with REPOSITORY_ROOT.joinpath("render.yaml").open(encoding="utf-8") as blueprint_file:
        blueprint = yaml.safe_load(blueprint_file)

    service = blueprint["services"][0]
    database = blueprint["databases"][0]

    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/healthz"
    assert service["region"] == database["region"]
    assert database["ipAllowList"] == []

    env_vars = {item["key"]: item for item in service["envVars"]}
    assert env_vars["OTARM_DATABASE_URL"]["fromDatabase"] == {
        "name": database["name"],
        "property": "connectionString",
    }
    assert env_vars["OTARM_DEMO_PASSWORD"]["sync"] is False
    assert env_vars["OTARM_TOKEN_SECRET"]["generateValue"] is True


def test_container_uses_render_port_with_local_fallback() -> None:
    dockerfile = REPOSITORY_ROOT.joinpath("Dockerfile").read_text(encoding="utf-8")

    assert '${PORT:-8000}' in dockerfile
