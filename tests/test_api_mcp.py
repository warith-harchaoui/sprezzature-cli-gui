"""
Tests for the HTTP and MCP surfaces.

The rendering itself is covered elsewhere; these guard the wiring, and one
thing more important than wiring: that the module-loading endpoint does not
exist. See :func:`test_no_route_loads_arbitrary_modules`.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
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


def _documented_routes(app):
    """This package's own tools -- fastapi-mcp mounts its transport route on
    the same app, and that one is not ours to document."""
    return [
        route
        for route in app.routes
        if getattr(route, "operation_id", None)
        and not getattr(route, "path", "").startswith("/mcp")
    ]


def test_every_tool_has_a_written_summary() -> None:
    """The first line an MCP host shows is FastAPI's `summary`, and its
    default is the function name title-cased: `cvd` became "Cvd", `wer`
    became "Wer". An agent choosing between tools from several servers reads
    those headlines and little else, so each has to be a written phrase
    saying what the tool does -- not a restatement of the Python identifier.
    """
    from sprezzature_cli_gui.api import app

    for route in _documented_routes(app):
        summary = (getattr(route, "summary", "") or "").strip()
        assert summary, f"{route.operation_id}: no summary, so the headline is a function name"
        derived = getattr(route, "name", "").replace("_", " ").title()
        assert summary != derived, (
            f"{route.operation_id}: summary {summary!r} is FastAPI's default (the "
            f"function name title-cased). Write one that says what the tool does."
        )
        assert " " in summary and len(summary) > 15, (
            f"{route.operation_id}: summary {summary!r} is too terse to route on."
        )


def test_every_tool_says_when_to_call_it() -> None:
    """A description that only restates the summary does not help an agent
    choose. Each route's docstring carries the deciding context: when to
    reach for it, what it needs first, or what it must not be used for.
    """
    from sprezzature_cli_gui.api import app

    for route in _documented_routes(app):
        description = (getattr(route, "description", "") or "").strip()
        assert len(description) > 120, (
            f"{route.operation_id}: description is {len(description)} chars. Say when "
            f"to call it, not just what it is."
        )
