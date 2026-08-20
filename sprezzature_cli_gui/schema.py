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
`Warith Harchaoui, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
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


def walk(obj: Any) -> dict[str, Any]:
    """
    Walk a CLI object (argparse or Click) into the canonical tree.

    Single entry point for the HTML renderer: it does not need to
    know which framework produced the input.

    Parameters
    ----------
    obj : argparse.ArgumentParser or click.Command
        The CLI to introspect.

    Returns
    -------
    dict
        Canonical parser tree (``prog``, ``description``, ``actions``,
        ``sub_commands``).

    Raises
    ------
    TypeError
        If ``obj`` is neither an argparse parser nor a Click command.
    """
    if isinstance(obj, argparse.ArgumentParser):
        # Lazy import keeps this module free of a top-level dependency
        # on the adapters package (which imports back from here).
        from sprezzature_cli_gui.adapters.argparse import walk_parser

        return walk_parser(obj)
    # Click is optional; only attempt the isinstance check after a
    # successful lazy import. Skipping the import on argparse-only
    # users keeps the script stdlib-only at run time.
    try:
        import click  # noqa: WPS433
    except ImportError:
        click = None  # type: ignore[assignment]
    if click is not None and isinstance(obj, click.Command):
        from sprezzature_cli_gui.adapters.click import walk_click

        return walk_click(obj)
    raise TypeError(
        f"walk() expected argparse.ArgumentParser or click.Command, got {type(obj).__name__}"
    )
