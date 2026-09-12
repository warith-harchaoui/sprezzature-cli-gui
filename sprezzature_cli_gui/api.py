"""
sprezzature-cli-gui: the FastAPI HTTP surface.

Module summary
--------------
Turns a command-line parser's *schema* into a working web form. The schema
is a plain JSON tree — ``prog``, ``description``, ``actions``,
``sub_commands`` — exactly what :func:`sprezzature_cli_gui.schema.walk`
produces from an ``argparse`` parser or a ``click`` command.

The one thing this surface deliberately will not do
----------------------------------------------------
It does **not** accept a ``module:factory`` spec.
:func:`sprezzature_cli_gui.loader.load_parser_from_spec` imports an
arbitrary file or module and calls the factory it names; behind an HTTP
endpoint that is unauthenticated remote code execution, and no amount of
allow-listing makes it safe enough to be worth it.

So the split is: **you** introspect your own parser, in your own process,
with the library — ``walk(parser)`` — and post the resulting tree here to
get the GUI back. The dangerous step never crosses the network, and the
part that does is a pure function of its input.

What ships here
---------------
- ``GET  /health``: a liveness probe.
- ``GET  /v1/example``: a small schema tree, so a caller can see the shape.
- ``POST /v1/render``: schema tree in, GUI HTML out.

Install the extra to get the runtime dependencies::

    pip install 'sprezzature-cli-gui[api]'

Then run the app with any ASGI server::

    uvicorn sprezzature_cli_gui.api:app --host 0.0.0.0 --port 8000

Usage example
-------------
>>> # In your own process, with your own parser:
>>> #   from sprezzature_cli_gui.schema import walk
>>> #   tree = walk(build_parser())
>>> # Then:
>>> #   curl -X POST localhost:8000/v1/render \\
>>> #        -H 'content-type: application/json' -d "{\\"tree\\": $tree}"
>>> # Full OpenAPI docs at http://localhost:8000/docs

Author
------
`Warith Harchaoui, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse, RedirectResponse
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError(
        "The FastAPI HTTP surface requires the [api] extra. "
        "Install with: pip install 'sprezzature-cli-gui[api]'"
    ) from exc

from pydantic import BaseModel, Field

from . import __version__ as _VERSION
from .renderer import render_html
from .schema import walk

app = FastAPI(
    title="Sprezzature CLI-GUI API",
    description=(
        "HTTP surface for sprezzature-cli-gui: turn a command-line parser's "
        "schema into a working web form. Schema in, HTML out."
    ),
    version=_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


class RenderRequest(BaseModel):
    """Body for ``POST /v1/render``."""

    tree: dict[str, Any] = Field(
        description=(
            "Parser schema, as sprezzature_cli_gui.schema.walk() returns: "
            "prog, description, actions, sub_commands."
        )
    )
    title: str = Field(default="CLI GUI", description="Page title for the generated GUI.")


def _example_tree() -> dict[str, Any]:
    """
    A small, real schema tree — walked from a real parser, not hand-written.

    Hand-writing the example would let it drift from what ``walk`` actually
    emits, which is exactly the kind of documentation that is worse than
    none. Building it from a throwaway parser keeps it honest.

    Returns
    -------
    dict
        The schema tree for a two-flag demo parser.
    """
    parser = argparse.ArgumentParser(prog="greet", description="Greet somebody.")
    parser.add_argument("--name", help="Who to greet.")
    parser.add_argument("--loud", action="store_true", help="Shout it.")
    return walk(parser)


@app.get("/health", tags=["meta"], operation_id="health")
def health() -> dict:
    """
    Liveness probe — no dependency check, just proves the app is up.

    Returns
    -------
    dict
        ``{"status": "ok"}``.
    """
    return {"status": "ok"}


@app.get("/v1/example", tags=["meta"], operation_id="get_example_schema")
def example() -> dict:
    """
    A small schema tree, so a caller can see the shape ``/v1/render`` wants.

    Returns
    -------
    dict
        ``{"tree": ...}`` for a two-flag demo parser.
    """
    return {"tree": _example_tree()}


@app.post("/v1/render", tags=["actions"], operation_id="render_gui", response_class=HTMLResponse)
def render(request: RenderRequest) -> HTMLResponse:
    """
    Render a parser schema as a self-contained GUI page.

    Parameters
    ----------
    request : RenderRequest
        The schema tree and a page title.

    Returns
    -------
    fastapi.responses.HTMLResponse
        The complete GUI page.

    Raises
    ------
    fastapi.HTTPException
        400 when the tree is missing the keys the renderer needs. Rendering
        a malformed tree would produce a plausible-looking but wrong form,
        which is worse than refusing.
    """
    missing = [k for k in ("prog", "actions") if k not in request.tree]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"schema tree is missing {missing}; see GET /v1/example for the shape",
        )
    return HTMLResponse(render_html(request.tree, title=request.title))


@app.get("/docs-redirect", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    """Convenience redirect to the interactive API docs."""
    return RedirectResponse(url="/docs")
