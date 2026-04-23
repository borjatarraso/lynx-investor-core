"""Tests for :mod:`lynx_investor_core.openapi`."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("flask")
from flask import Flask

from lynx_investor_core import openapi


@pytest.fixture()
def app() -> Flask:
    a = Flask(__name__)

    @a.route("/api/hello", methods=["GET"])
    def hello():
        """Hello world.

        Returns a greeting.
        """
        return {"hello": "world"}

    @a.route("/api/items/<int:item_id>", methods=["GET", "DELETE"])
    def item(item_id: int):
        """Single item detail."""
        return {"id": item_id}

    @a.route("/api/items", methods=["POST"])
    def create_item():
        return {"ok": True}

    return a


class TestRuleToOpenAPIPath:
    def test_no_params(self) -> None:
        assert openapi._rule_to_openapi_path("/api/foo") == "/api/foo"

    def test_typed_param(self) -> None:
        assert openapi._rule_to_openapi_path("/api/x/<int:id>") == "/api/x/{id}"

    def test_bare_param(self) -> None:
        assert openapi._rule_to_openapi_path("/api/<ticker>") == "/api/{ticker}"

    def test_multiple_params(self) -> None:
        out = openapi._rule_to_openapi_path("/api/<int:a>/child/<b>")
        assert out == "/api/{a}/child/{b}"


class TestParamsFromRule:
    def test_typed_integer(self) -> None:
        p = openapi._params_from_rule("/api/x/<int:id>")
        assert p == [{
            "name": "id", "in": "path", "required": True,
            "schema": {"type": "integer"},
        }]

    def test_bare_is_string(self) -> None:
        p = openapi._params_from_rule("/api/<ticker>")
        assert p[0]["schema"]["type"] == "string"

    def test_no_params(self) -> None:
        assert openapi._params_from_rule("/api/foo") == []


class TestBuildSpec:
    def test_top_level_fields(self, app: Flask) -> None:
        spec = openapi.build_openapi_spec(
            app, title="X", version="1.0", description="test",
        )
        assert spec["openapi"].startswith("3.1")
        assert spec["info"]["title"] == "X"
        assert spec["info"]["version"] == "1.0"

    def test_enumerates_every_route(self, app: Flask) -> None:
        spec = openapi.build_openapi_spec(app, title="X", version="1.0")
        assert "/api/hello" in spec["paths"]
        assert "/api/items/{item_id}" in spec["paths"]
        assert "/api/items" in spec["paths"]

    def test_methods_listed(self, app: Flask) -> None:
        spec = openapi.build_openapi_spec(app, title="X", version="1.0")
        assert "get" in spec["paths"]["/api/hello"]
        assert "get" in spec["paths"]["/api/items/{item_id}"]
        assert "delete" in spec["paths"]["/api/items/{item_id}"]
        assert "post" in spec["paths"]["/api/items"]

    def test_docstring_surfaced(self, app: Flask) -> None:
        spec = openapi.build_openapi_spec(app, title="X", version="1.0")
        hello_op = spec["paths"]["/api/hello"]["get"]
        assert hello_op["summary"] == "Hello world"
        assert "greeting" in hello_op["description"]

    def test_bearer_auth_configured(self, app: Flask) -> None:
        spec = openapi.build_openapi_spec(app, title="X", version="1.0")
        assert "BearerAuth" in spec["components"]["securitySchemes"]
        assert spec["security"] == [{"BearerAuth": []}]


class TestMount:
    def test_mount_adds_two_routes(self, app: Flask) -> None:
        openapi.mount_openapi(app, title="X", version="1.0")
        rules = {r.rule for r in app.url_map.iter_rules()}
        assert "/api/openapi.json" in rules
        assert "/api/docs" in rules

    def test_spec_endpoint_returns_valid_json(self, app: Flask) -> None:
        openapi.mount_openapi(app, title="X", version="1.0")
        with app.test_client() as c:
            rv = c.get("/api/openapi.json")
            assert rv.status_code == 200
            data = json.loads(rv.data)
            assert data["info"]["title"] == "X"

    def test_docs_endpoint_returns_html(self, app: Flask) -> None:
        openapi.mount_openapi(app, title="X", version="1.0")
        with app.test_client() as c:
            rv = c.get("/api/docs")
            assert rv.status_code == 200
            assert b"swagger-ui" in rv.data
            assert b"/api/openapi.json" in rv.data
