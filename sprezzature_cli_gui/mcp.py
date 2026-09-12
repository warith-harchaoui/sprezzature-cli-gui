"""
sprezzature-cli-gui — Model Context Protocol (MCP) surface.

Adapter that republishes the FastAPI app in :mod:`sprezzature_cli_gui.api`
as MCP tools, so any MCP-aware host — an agent runtime, an IDE integration,
a custom shell — can call ``check_contrast`` / ``simulate_color_blindness``
/ ``get_palette`` as first-class tools instead of guessing at a shell
command. Uses :mod:`fastapi_mcp` (https://github.com/tadata-org/fastapi_mcp):
one wrapper over the whole existing HTTP surface, so the routes serve both
plain HTTP callers and MCP hosts without being written twice.

Why a wrapper rather than a hand-written server
-----------------------------------------------
A hand-written MCP server would be a second description of the same
surface, free to drift from the routes it claims to mirror — a tool whose
argument names quietly disagree with the API is worse than no tool, because
the disagreement only shows up at call time. Deriving the tools from the
FastAPI signatures means the two cannot disagree: the ``operation_id`` on
each route *is* the tool name, and the Pydantic model *is* the schema.

Why colour checks are worth giving an agent
--------------------------------------------
These are questions with defensible answers rather than opinions. A contrast
ratio is defined by WCAG; a colour-vision simulation is a published matrix.
An assistant asked "is this palette accessible?" can now answer with a
number it computed instead of an impression it formed — and be wrong in a
way that is checkable.

Install the extra to pull in ``fastapi-mcp``::

    pip install 'sprezzature-cli-gui[api,mcp]'

Then run the MCP server::

    sprezzature-cli-gui-mcp          # entry point (see pyproject)
    # or, equivalently:
    python -m sprezzature_cli_gui.mcp

Usage Example
-------------
>>> # Register the MCP endpoint in your client. It publishes:
>>> #   health / get_example_schema / render_gui
>>> # ...with the same argument names as the FastAPI routes.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys

try:
    from fastapi_mcp import FastApiMCP
except ImportError:  # pragma: no cover - dependency guard

    def main() -> None:
        """
        Entry point when the MCP extra is not installed.

        Says which extra is missing and stops. Reaching an MCP
        command without the ``[mcp]`` extra needs a one-line fix,
        not a stack trace.
        """
        print(
            "sprezzature-cli-gui MCP surface requires fastapi-mcp. "
            "Install with: pip install 'sprezzature-cli-gui[api,mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)

else:

    # Reuse the exact same FastAPI app -- MCP is a thin wrapper on top.
    from sprezzature_cli_gui.api import app

    # FastApiMCP mounts an MCP endpoint on the existing FastAPI app; the wrapped
    # instance is kept at module scope so downstream code (tests, ASGI runners)
    # can reach both the FastAPI app and the MCP handler.
    mcp = FastApiMCP(
        app,
        name="sprezzature-cli-gui",
        description=(
            "Sprezzature CLI-GUI MCP tools: turn a command-line parser schema "
            "into a working web form. Schema in, HTML out — never a module path."
        ),
        include_tags=["meta", "actions"],
    )
    # Newer fastapi-mcp releases split mount() into transport-specific
    # mount_http() (recommended) and mount_sse(); fall back to the legacy
    # mount() on older versions so a range of fastapi-mcp versions still work.
    if hasattr(mcp, "mount_http"):
        mcp.mount_http()
    else:  # pragma: no cover - legacy fastapi-mcp
        mcp.mount()


    def main() -> None:
        """
        Entry point for the ``sprezzature-cli-gui-mcp`` console script.

        Boots the FastAPI app — which now serves both the HTTP routes and the
        MCP endpoint — with ``uvicorn``. Meant for local or container usage;
        behind a real load balancer, run ``uvicorn``/``gunicorn`` directly.
        """
        import os

        import uvicorn

        host = os.environ.get("SPREZZATURE_CLI_GUI_HOST", "0.0.0.0")
        port = int(os.environ.get("SPREZZATURE_CLI_GUI_PORT", "8000"))
        uvicorn.run(app, host=host, port=port, workers=1)

if __name__ == "__main__":  # pragma: no cover
    main()
