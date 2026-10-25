from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _compose(name: str) -> dict:
    with REPOSITORY_ROOT.joinpath(name).open(encoding="utf-8") as compose_file:
        return yaml.safe_load(compose_file)


def _workflow(name: str) -> dict:
    workflow_path = REPOSITORY_ROOT.joinpath(".github", "workflows", name)
    with workflow_path.open(encoding="utf-8") as workflow_file:
        return yaml.load(workflow_file, Loader=yaml.BaseLoader)


def test_production_compose_is_independent_from_development() -> None:
    development = _compose("docker-compose.yaml")
    production = _compose("docker-compose.production.yaml")

    assert production["name"] == "otarm-production"
    assert production["volumes"].keys().isdisjoint(development["volumes"].keys())
    assert production["services"]["app"]["ports"] == ["${OTARM_PROD_PORT:-8080}:8000"]
    assert production["services"]["db"]["environment"]["POSTGRES_DB"] == "otarm_production"
    assert production["services"]["db"]["environment"]["POSTGRES_USER"] == "otarm_production"


def test_production_uses_a_pinned_external_image_and_separate_secrets() -> None:
    production = _compose("docker-compose.production.yaml")
    app = production["services"]["app"]
    database = production["services"]["db"]

    assert "build" not in app
    assert app["image"].startswith("${OTARM_IMAGE:?")
    assert "OTARM_PROD_POSTGRES_PASSWORD" in app["environment"]["OTARM_DATABASE_URL"]
    assert "OTARM_PROD_DEMO_PASSWORD" in app["environment"]["OTARM_DEMO_PASSWORD"]
    assert "OTARM_PROD_TOKEN_SECRET" in app["environment"]["OTARM_TOKEN_SECRET"]
    assert "OTARM_PROD_POSTGRES_PASSWORD" in database["environment"]["POSTGRES_PASSWORD"]
    assert app["read_only"] is True
    assert production["networks"]["production-internal"]["internal"] is True


def test_production_promotion_is_manual_and_does_not_rebuild() -> None:
    workflow = _workflow("promote-production.yml")
    promotion = workflow["jobs"]["promote"]
    serialized_steps = yaml.safe_dump(promotion["steps"])

    assert list(workflow["on"]) == ["workflow_dispatch"]
    assert workflow["permissions"] == {"contents": "read", "packages": "write"}
    assert workflow["concurrency"]["cancel-in-progress"] == "false"
    assert promotion["environment"]["name"] == "render-production"
    assert "docker buildx imagetools create" in serialized_steps
    assert "build-push-action" not in serialized_steps
    assert "^sha-[0-9a-f]{40}$" in serialized_steps


