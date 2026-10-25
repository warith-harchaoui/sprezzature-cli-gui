"""
sprezzature_cli_gui.schema
===================

The one shape every CLI framework gets flattened into, and the function
that does the flattening.

Whichever of the three supported frameworks built the target CLI, this
module reduces it to the same plain dict shape (``prog`` / ``description`` /
``actions`` / ``sub_commands``), so the renderer that builds the HTML page
never has to know or care which framework it came from. This module holds
the pieces every adapter shares (a sentinel value marking "no default was
given", and a helper that makes a default JSON-serialisable), plus
:func:`walk`, the single entry point the rest of the package calls.

:func:`walk` imports the actual per-framework adapters only when it runs,
inside the function body rather than at the top of this file. That keeps
this module's own imports free of any dependency on
:mod:`sprezzature_cli_gui.adapters`, which avoids a circular import: the
adapters need this module's shared helpers, and if this module imported
them back at load time, the two would need each other before either had
finished loading.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
from typing import Any

#: Sentinel returned by :func:`_safe_default` for defaults we cannot
#: safely serialise to JSON. The HTML treats it as "no default
#: published" and leaves the form field empty.
NO_DEFAULT: object = object()


def _safe_default(default: Any) -> Any:
    """Return a JSON-serialisable representation of an argparse default."""
    if default is argparse.SUPPRESS or default is None:
        return None
    if isinstance(default, (str, int, float, bool)):
        return default
    if isinstance(default, (list, tuple)):
        return [_safe_default(d) for d in default]
    return str(default)


def walk(obj: Any, *, prog: str | None = None) -> dict[str, Any]:
    """
    Walk a CLI object (argparse, Click or Typer) into the canonical tree.

    Single entry point for the HTML renderer: it does not need to
    know which framework produced the input.

    Parameters
    ----------
    obj : argparse.ArgumentParser, click.Command or typer.Typer
        The CLI to introspect. A ``typer.Typer`` is converted with typer's own
        ``get_command`` and then walked as Click, because that is what it
        becomes; there is no third adapter.
    prog : str or None, optional
        Override the top-level ``prog`` field, which both the page
        header and the built command line are seeded from. Needed
        because a Click ``Group`` has no equivalent of argparse's
        explicit ``prog=`` kwarg: its own ``name`` defaults to the
        decorated function's name (e.g. ``main``), which is usually
        not the installed console-script name (e.g.
        ``sprezzature-maps``). Left unset, that mismatch means the
        page's "Build command" output assembles a command line that
        does not exist. Only affects the root of the tree; a
        sub-command's own name is unaffected.

    Returns
    -------
    dict
        Canonical parser tree (``prog``, ``description``, ``actions``,
        ``sub_commands``).

    Raises
    ------
    TypeError
        If ``obj`` is none of the three. The message names what was passed,
        because the common mistake is handing over the *module* or the
        *function* rather than the parser.
    """
    if isinstance(obj, argparse.ArgumentParser):
        # Lazy import keeps this module free of a top-level dependency
        # on the adapters package (which imports back from here).
        from sprezzature_cli_gui.adapters.argparse import walk_parser

        tree = walk_parser(obj)
        if prog is not None:
            tree["prog"] = prog
        return tree
    # Click is optional; only attempt the isinstance check after a
    # successful lazy import. Skipping the import on argparse-only
    # users keeps the script stdlib-only at run time.
    try:
        import click  # noqa: WPS433
    except ImportError:
        click = None  # type: ignore[assignment]
    if click is not None and isinstance(obj, click.Command):
        from sprezzature_cli_gui.adapters.click import walk_click

        return walk_click(obj, prog=prog)
    # A Typer app is NOT a click.Command -- typer builds one on demand -- so it
    # reached the refusal below and the documented support was a claim only.
    #
    # The route this adapter's own docstring named, ``app.cli``, does not exist
    # on typer 0.20: checked, not assumed. ``typer.main.get_command`` is the
    # supported conversion and returns a ``TyperCommand``, which *is* a
    # ``click.Command`` -- so the result goes through the Click adapter rather
    # than growing a third one for a framework that is Click underneath.
    try:
        import typer  # noqa: WPS433
    except ImportError:
        typer = None  # type: ignore[assignment]
    if typer is not None and isinstance(obj, typer.Typer):
        from typer.main import get_command

        from sprezzature_cli_gui.adapters.click import walk_click

        return walk_click(get_command(obj), prog=prog)

    raise TypeError(
        "walk() expected argparse.ArgumentParser, click.Command or typer.Typer, "
        f"got {type(obj).__name__}"
    )
