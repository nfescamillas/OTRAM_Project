from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _workflow(name: str) -> dict:
    with REPOSITORY_ROOT.joinpath(".github", "workflows", name).open(
        encoding="utf-8"
    ) as workflow_file:
        return yaml.load(workflow_file, Loader=yaml.BaseLoader)


def test_render_blueprint_wires_web_service_to_private_database() -> None:
    with REPOSITORY_ROOT.joinpath("render.yaml").open(encoding="utf-8") as blueprint_file:
        blueprint = yaml.safe_load(blueprint_file)

    service = blueprint["services"][0]
    database = blueprint["databases"][0]

    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/healthz"
    assert service["autoDeployTrigger"] == "off"
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


def test_manual_promotion_deploys_the_selected_revision_to_render() -> None:
    ci_workflow = _workflow("ci.yml")
    workflow = _workflow("promote-production.yml")
    deployment = workflow["jobs"]["promote"]
    serialized_steps = yaml.safe_dump(deployment["steps"])
    trigger_step = next(step for step in deployment["steps"] if step.get("id") == "deploy")
    health_step = next(step for step in deployment["steps"] if step.get("id") == "health")

    assert "deploy-render" not in ci_workflow["jobs"]
    assert list(workflow["on"]) == ["workflow_dispatch"]
    assert deployment["environment"]["name"] == "render-production"
    assert workflow["permissions"] == {"contents": "read", "packages": "write"}
    assert "RENDER_DEPLOY_HOOK_URL" in serialized_steps
    assert "RENDER_SERVICE_URL" in serialized_steps
    assert '--data-urlencode "ref=$SOURCE_SHA"' in trigger_step["run"]
    assert "/healthz" in health_step["run"]
    assert '.revision == $expected_revision' in health_step["run"]
    assert '--arg expected_revision "$SOURCE_SHA"' in health_step["run"]
