from pathlib import Path

import yaml

from app.main import create_app


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def test_implemented_paths_and_operations_match_root_contract() -> None:
    contract = yaml.safe_load((Path(__file__).parents[2] / "openapi.yaml").read_text(encoding="utf-8"))
    generated = create_app(database_url="sqlite:///:memory:").openapi()

    contract_operations = {
        (f"/api/v1{path}", method, operation["operationId"])
        for path, path_item in contract["paths"].items()
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    }
    generated_operations = {
        (path, method, operation["operationId"])
        for path, path_item in generated["paths"].items()
        if path.startswith("/api/v1")
        for method, operation in path_item.items()
        if method in HTTP_METHODS
    }

    assert generated_operations == contract_operations


def test_only_token_exchange_is_unauthenticated() -> None:
    contract = yaml.safe_load((Path(__file__).parents[2] / "openapi.yaml").read_text(encoding="utf-8"))
    for path, path_item in contract["paths"].items():
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            expected = [] if path == "/auth/token" else [{"bearerAuth": []}]
            assert operation["security"] == expected, f"Unexpected authentication declaration for {method} {path}"
