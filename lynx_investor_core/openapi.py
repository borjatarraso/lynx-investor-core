"""OpenAPI / Swagger-UI helpers for Suite Flask apps.

Every Flask app in the Suite can opt into a machine-readable API
description with **one function call**:

```python
from lynx_investor_core.openapi import mount_openapi

mount_openapi(
    app,
    title="Lynx Portfolio API",
    version="5.3",
    description="Portfolio + dashboard REST endpoints.",
)
```

This installs two extra routes:

* ``GET /api/openapi.json`` — a valid OpenAPI 3.1 document. Built by
  inspecting Flask's ``url_map`` and each route's docstring; no
  decorators required on the routes themselves.
* ``GET /api/docs`` — a self-contained HTML page that renders the
  document via the Swagger UI CDN (no server-side dependency).

The document is intentionally light. It enumerates every route, the
HTTP methods it accepts, the path parameters, and (when the Flask view
function has a docstring) a short summary + description. It does NOT
try to infer request / response schemas — for richer specs, extend
the generator below.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Flask, Response, jsonify


__all__ = ["build_openapi_spec", "mount_openapi"]


# ---------------------------------------------------------------------------
# Spec builder
# ---------------------------------------------------------------------------

_EXCLUDE_RULES = {
    "/static/<path:filename>",           # Flask default
    "/web/<path:filename>",              # lynx-portfolio static mount
}


def _rule_to_openapi_path(rule: str) -> str:
    """Convert Flask ``/api/foo/<int:id>`` → OpenAPI ``/api/foo/{id}``."""
    out = []
    depth = 0
    buf = ""
    for ch in rule:
        if ch == "<":
            depth += 1
            buf = ""
            continue
        if ch == ">":
            depth -= 1
            # buf looks like "int:id" or just "id"
            name = buf.split(":", 1)[-1]
            out.append("{" + name + "}")
            buf = ""
            continue
        if depth > 0:
            buf += ch
        else:
            out.append(ch)
    return "".join(out)


def _params_from_rule(rule: str) -> List[Dict[str, Any]]:
    params = []
    depth = 0
    buf = ""
    for ch in rule:
        if ch == "<":
            depth += 1; buf = ""; continue
        if ch == ">":
            depth -= 1
            if ":" in buf:
                kind, name = buf.split(":", 1)
            else:
                kind, name = "string", buf
            schema_type = {"int": "integer", "float": "number",
                           "path": "string", "uuid": "string",
                           "string": "string"}.get(kind, "string")
            params.append({
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": schema_type},
            })
            buf = ""; continue
        if depth > 0:
            buf += ch
    return params


def _describe_view(view_fn) -> Dict[str, str]:
    doc = (view_fn.__doc__ or "").strip()
    if not doc:
        return {"summary": view_fn.__name__.replace("_", " ")}
    first_line, _, rest = doc.partition("\n")
    return {
        "summary": first_line.strip().rstrip("."),
        "description": rest.strip() or first_line.strip(),
    }


def build_openapi_spec(
    app: Flask,
    *,
    title: str,
    version: str,
    description: str = "",
    servers: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Inspect *app*'s url_map and return an OpenAPI 3.1 dict."""
    paths: Dict[str, Dict[str, Any]] = {}
    for rule in app.url_map.iter_rules():
        if rule.rule in _EXCLUDE_RULES:
            continue
        path = _rule_to_openapi_path(rule.rule)
        entry = paths.setdefault(path, {})
        view = app.view_functions.get(rule.endpoint)
        desc = _describe_view(view) if view else {"summary": rule.endpoint}
        path_params = _params_from_rule(rule.rule)
        for method in sorted(rule.methods - {"OPTIONS", "HEAD"}):
            op = {
                "operationId": f"{rule.endpoint}_{method.lower()}",
                **desc,
                "responses": {
                    "200": {"description": "Success"},
                    "401": {"description": "Unauthorized"},
                    "400": {"description": "Bad request"},
                    "404": {"description": "Not found"},
                    "500": {"description": "Internal server error"},
                },
            }
            if path_params:
                op["parameters"] = path_params
            entry[method.lower()] = op

    spec: Dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "license": {
                "name": "BSD-3-Clause",
                "identifier": "BSD-3-Clause",
            },
        },
        "servers": servers or [{"url": "/"}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "opaque",
                },
            },
        },
        "security": [{"BearerAuth": []}],
    }
    return spec


# ---------------------------------------------------------------------------
# Swagger-UI HTML (self-contained — CDN-hosted JS & CSS)
# ---------------------------------------------------------------------------

_SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — API docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>
    body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    .swagger-ui .topbar {{ display: none; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({{
      url: "{spec_url}",
      dom_id: "#swagger-ui",
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis],
      layout: "BaseLayout",
      persistAuthorization: true,
    }});
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Mount helper
# ---------------------------------------------------------------------------

def mount_openapi(
    app: Flask,
    *,
    title: str,
    version: str,
    description: str = "",
    spec_path: str = "/api/openapi.json",
    docs_path: str = "/api/docs",
    servers: Optional[List[Dict[str, str]]] = None,
) -> None:
    """Install the ``/openapi.json`` + ``/docs`` routes on *app*."""
    @app.route(spec_path, methods=["GET"])
    def _openapi_spec():
        """Machine-readable OpenAPI 3.1 description of every API route."""
        return jsonify(build_openapi_spec(
            app, title=title, version=version,
            description=description, servers=servers,
        ))

    @app.route(docs_path, methods=["GET"])
    def _api_docs():
        """Human-readable Swagger UI rendering of the OpenAPI spec."""
        html = _SWAGGER_HTML.format(title=title, spec_url=spec_path)
        return Response(html, mimetype="text/html")
