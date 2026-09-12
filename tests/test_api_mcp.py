"""
Tests for the HTTP and MCP surfaces.

The rendering itself is covered elsewhere; these guard the wiring, and one
thing more important than wiring: that the module-loading endpoint does not
exist. See :func:`test_no_route_loads_arbitrary_modules`.

Author
------
`Warith Harchaoui, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from sprezzature_cli_gui.api import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    """The liveness probe answers."""
    assert client.get("/health").json() == {"status": "ok"}


def test_example_is_a_real_walked_tree() -> None:
    """The example comes from walk(), so it cannot drift from the real shape."""
    tree = client.get("/v1/example").json()["tree"]
    assert {"prog", "description", "actions", "sub_commands"} <= set(tree)
    assert tree["actions"], "an example with no actions teaches nothing"


def test_render_returns_a_page() -> None:
    """A valid tree renders to HTML carrying the title it was given."""
    tree = client.get("/v1/example").json()["tree"]
    response = client.post("/v1/render", json={"tree": tree, "title": "Greet"})
    assert response.status_code == 200
    assert "Greet" in response.text
    assert "<form" in response.text or "<input" in response.text


def test_malformed_tree_is_rejected() -> None:
    """
    Rendering a tree missing its keys would produce a plausible-looking but
    wrong form, which is worse than refusing outright.
    """
    assert client.post("/v1/render", json={"tree": {"nope": 1}}).status_code == 400


def test_no_route_loads_arbitrary_modules() -> None:
    """
    No endpoint may accept a ``module:factory`` spec.

    ``loader.load_parser_from_spec`` imports an arbitrary file or module and
    calls the factory it names. Reachable over HTTP that is unauthenticated
    remote code execution. This test fails if anyone ever adds such a route,
    which is the only moment the mistake is cheap to undo.
    """
    schema = client.get("/openapi.json").json()
    blob = str(schema).lower()
    for forbidden in ("load_parser", "module_spec", '"spec"'):
        assert forbidden not in blob, f"{forbidden!r} appears in the public schema"


def test_openapi_names_every_tool() -> None:
    """Each route carries an operation_id: that *is* the MCP tool name."""
    paths = client.get("/openapi.json").json()["paths"]
    for path, methods in paths.items():
        for verb, spec in methods.items():
            assert "operationId" in spec, f"{verb.upper()} {path} has no operation_id"


def test_mcp_mounts_and_publishes_the_tools() -> None:
    """The MCP endpoint exists and carries the expected tool names."""
    pytest.importorskip("fastapi_mcp")
    from sprezzature_cli_gui.mcp import mcp

    assert mcp is not None
    mounted = {getattr(r, "path", "") for r in app.routes}
    assert any(p.startswith("/mcp") for p in mounted), sorted(mounted)
    assert "render_gui" in {t.name for t in mcp.tools}
