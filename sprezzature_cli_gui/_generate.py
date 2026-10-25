#!/usr/bin/env python3
"""
The work behind the command line: a CLI spec in, a page or a tree out.

Lifted out of the argparse front door on 2026-10-25, when click became the only
parser. It was the body of ``cli.main`` and therefore reachable only by parsing
an argument vector — which is why the click twin used to rebuild an argv and
call the argparse ``main`` through it, a wrapper around a parser around the
work. The work lives here now, and the command line calls it directly.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sprezzature_cli_gui.adapters.help_text import walk_from_help
from sprezzature_cli_gui.loader import load_parser_from_spec
from sprezzature_cli_gui.renderer import render_html
from sprezzature_cli_gui.schema import walk


class GenerationError(RuntimeError):
    """
    A spec that could not be read, walked or written.

    One exception type rather than the four the two front doors used to catch
    separately: the caller needs to say one sentence and stop, and which of
    ``ValueError`` / ``ImportError`` / ``AttributeError`` arrived is detail the
    message already carries.
    """


def build_tree(spec: str, *, from_help: bool = False, prog: str | None = None) -> dict[str, Any]:
    """
    Walk a CLI into the tree the renderer reads.

    Parameters
    ----------
    spec : str
        ``module:factory`` for introspection, or a shell command line when
        *from_help* is set.
    from_help : bool
        Read the CLI's own ``--help`` in a subprocess instead of importing it.
        The escape hatch for a CLI that cannot be imported.
    prog : str or None
        Override the program name the page announces.

    Returns
    -------
    dict
        The walked parser.

    Raises
    ------
    GenerationError
        If the spec cannot be found, imported, or walked.
    """
    if from_help:
        try:
            return walk_from_help(spec)
        except (FileNotFoundError, OSError) as exc:
            raise GenerationError(f"--from-help failed: {exc}") from exc
    try:
        cli_obj: Any = load_parser_from_spec(spec)
    except (ValueError, FileNotFoundError, ImportError, AttributeError) as exc:
        raise GenerationError(str(exc)) from exc
    try:
        return walk(cli_obj, prog=prog)
    except TypeError as exc:
        raise GenerationError(str(exc)) from exc


def render(tree: dict[str, Any], *, as_json: bool = False, title: str | None = None) -> str:
    """Render a walked tree as the single-page GUI, or as JSON for debugging."""
    if as_json:
        return json.dumps(tree, indent=2, ensure_ascii=False) + "\n"
    return render_html(tree, title=title or tree["prog"])


def write(output: str, out: Path | None) -> str | None:
    """
    Write *output* to *out*, or return it for the caller to print.

    Returns
    -------
    str or None
        The path written, or ``None`` when the caller should print to stdout.

    Raises
    ------
    GenerationError
        If the write fails. A page that was generated and not saved is a
        success the user cannot use.
    """
    if out is None:
        return None
    try:
        out.write_text(output, encoding="utf-8")
    except OSError as exc:
        raise GenerationError(f"write failed: {exc}") from exc
    return str(out)
