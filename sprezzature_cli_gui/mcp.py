"""
sprezzature-cli-gui — Model Context Protocol (MCP) surface.

Adapter that republishes the FastAPI app in :mod:`sprezzature_cli_gui.api`
as MCP tools, so any MCP-aware host — an agent runtime, an IDE integration,
a custom shell — can call ``health`` / ``get_example_schema`` /
``render_gui`` / ``audit_gui`` as first-class tools instead of guessing at a
shell command. Uses :mod:`fastapi_mcp` (https://github.com/tadata-org/fastapi_mcp):
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

Why these tools are worth giving an agent
-----------------------------------------
They take a schema tree and never a ``module:factory`` spec, so no tool
imports or runs the user's code. An agent asked for "a form for this CLI"
can render one from a tree it walked or wrote, and check a page against a
tree with ``audit_gui``, without being handed remote code execution.

``fastapi-mcp`` is a base dependency since 2026-11-01, so there is no
extra to ask for::

    pip install 'sprezzature-cli-gui'

Then run the MCP server::

    sprezzature-cli-gui-mcp          # entry point (see pyproject)
    # or, equivalently:
    python -m sprezzature_cli_gui.mcp

Usage Example
-------------
>>> # Register the MCP endpoint in your client. It publishes:
>>> #   health / get_example_schema / render_gui / audit_gui
>>> # ...with the same argument names as the FastAPI routes, at /mcp.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys

try:
    from fastapi_mcp import FastApiMCP
except ImportError:  # pragma: no cover - dependency guard

    def main(argv: list[str] | None = None) -> None:
        """
        Entry point when fastapi-mcp cannot be imported.

        Takes the same ``argv`` as the real entry point and ignores it:
        the two variants are reached through the same console script, so
        a caller that passes arguments must not get a ``TypeError`` from
        the branch that happens to be missing a dependency.

        Says the install is broken and stops. fastapi-mcp is a base
        dependency, so a missing one needs a one-line reinstall, not a
        stack trace.
        """
        print(
            "sprezzature-cli-gui MCP surface could not import fastapi-mcp, which is a "
            "base dependency since 2026-11-01 -- a broken install rather than "
            "a missing extra. Reinstall with: "
            "pip install 'sprezzature-cli-gui'",
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

    def main(argv: list[str] | None = None) -> None:
        """
        Entry point for the ``sprezzature-cli-gui-mcp`` console script.

        Serves the FastAPI app — which carries both the HTTP routes and the
        MCP endpoint — with ``uvicorn``, in single-worker mode. Meant for
        local or container use; behind a real load balancer, run ``uvicorn``
        or ``gunicorn`` directly.

        Arguments are parsed before anything is bound, so ``--help`` answers
        instead of starting a server and hanging.

        Parameters
        ----------
        argv : list of str or None, optional
            Arguments to parse. ``None`` reads ``sys.argv``.
        """
        import argparse
        import os

        parser = argparse.ArgumentParser(
            prog="sprezzature-cli-gui-mcp",
            description=(
                "Serve the sprezzature-cli-gui MCP tools over HTTP. Every tool is a "
                "route on the same FastAPI app, with the MCP endpoint "
                "mounted beside them."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "Defaults come from SPREZZATURE_CLI_GUI_HOST and "
                "SPREZZATURE_CLI_GUI_PORT when those are set.\n"
                "The host defaults to 127.0.0.1: pass --host 0.0.0.0 to "
                "accept connections from outside this machine."
            ),
        )
        parser.add_argument(
            "--host",
            default=os.environ.get("SPREZZATURE_CLI_GUI_HOST", "127.0.0.1"),
            help="Interface to bind (default: %(default)s).",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=int(os.environ.get("SPREZZATURE_CLI_GUI_PORT", "8000")),
            help="Port to bind (default: %(default)s).",
        )
        args = parser.parse_args(argv)

        import uvicorn

        uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":  # pragma: no cover
    main()
