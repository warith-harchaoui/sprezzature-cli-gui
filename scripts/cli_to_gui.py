#!/usr/bin/env python3
"""
cli_to_gui
==========

Read a Python command-line tool's own parser object and emit a single-page
web form (plain JavaScript, styled with Tailwind's utility classes) that
maps every sub-command and flag to a field. The output follows this
project's own house rules for generated pages, so the emitted file can be
dropped as is into an internal tool, into a `Tauri` desktop app's embedded
browser view, or onto a plain static-file host.

This is the generating half of the ``sprezzature-cli-gui`` skill, alongside
sibling skills elsewhere in the ``sprezzature-*`` collection such as
``audit_laws_of_ux.py`` and ``palette_to_tailwind.py``. It is not a runtime
that executes the target command: the emitted page only builds the command
line as text, locally, in the visitor's browser, and displays it ready to
copy, paste, or hand to whatever actually runs it (a FastAPI server over
SSE, meaning Server-Sent Events, a plain one-way stream a server uses to
push output back to a page; a `Tauri` app through its ``invoke()`` bridge;
an Express server; or a plain shell).

Supported source frameworks
---------------------------

The emitter itself never has to know which framework built the target CLI:
a small adapter, one per framework, reduces each to the same plain
parser-tree dict (``prog`` / ``description`` / ``actions`` /
``sub_commands``), and everything downstream reads only that shape. Three
adapters ship today:

- **argparse** (in Python's standard library, so always available). Reads
  an :class:`argparse.ArgumentParser` with :func:`walk_parser`, used
  whenever the target factory returns one.
- **Click** (an optional third-party dependency, only imported when
  actually needed). Reads a :class:`click.Command` with :func:`walk_click`.
  `Typer` apps are covered too, through the Click group Typer builds
  internally (``app.cli``).
- **``--from-help``** (framework-agnostic). Runs the target command with
  ``--help`` and parses the printed text instead of a live parser object,
  with :func:`walk_from_help`. This is the fallback for a CLI written in
  another language entirely (Rust's `clap`, Go's `cobra`, Node's
  `commander`) or one whose Python parser cannot be imported for some
  reason.

Adding a fourth framework later only means writing one more adapter that
produces the same dict; the renderer that turns the dict into HTML never
has to change.

Why read the parser object, not just its ``--help`` text?
-----------------------------------------------------------

``--help`` text is meant for a person to read, not a program to parse: its
exact wording shifts with the formatter, the terminal width, and the
locale, so parsing it is inherently best-effort. A live parser object, by
contrast, carries the tool's actual structured truth: its real choice
lists, its ``type=`` conversion functions, which flags are required, and
their real default values. Reading the object directly is preferred
whenever it is reachable; the ``--from-help`` adapter above exists
precisely for the cases where it is not, and it recovers correspondingly
less: every option becomes a plain text field unless the help line spells
out a default value (``[default: …]``) or something similar.

Inputs
------

The caller names a parser factory with a ``SPEC`` string, in one of two
forms:

- ``path/to/file.py:make_parser``: load that file as a standalone module,
  then call its ``make_parser()`` function.
- ``my_pkg.my_cli:build_parser``: import the dotted module path instead,
  then call the named factory function inside it.

Either way, the factory must take no arguments and return either an
:class:`argparse.ArgumentParser` or a :class:`click.Command`. Which adapter
reads the result is then chosen automatically, from the returned object's
own type.

Outputs
-------

A single HTML file: printed to standard output by default, or written to
disk when ``--out PATH`` is given. It contains:

- Tailwind loaded from its "Play" CDN build (a version meant for quick
  prototypes, fetched straight from a public URL with no local build step).
  This is the page's one runtime network dependency; the form fields still
  work, unstyled, if that request fails.
- A sticky header showing the parser's program name and description.
- One collapsed ``<details>`` block per sub-command, or a single form when
  the CLI has none, with a field for every flag.
- A "Build command" button that assembles the full command line from the
  filled-in form and prints it into a ``<pre>`` block, ready to copy or to
  hand to a `Tauri` ``invoke()`` call.
- A working dark-mode variant on every styled element, a visible focus
  ring, and respect for ``prefers-reduced-motion``, all required by this
  project's own house rules for generated pages.

Stack rules respected
---------------------

- Plain JavaScript only, as an ES module (the standard, import/export-based
  module format modern browsers support natively); no React, Vue, or
  Svelte.
- Styling built only from Tailwind's utility classes; no raw hex color
  codes written directly in the markup.
- Semantic HTML tags throughout (``<form>``, ``<label for>``, ``<button>``,
  ``<details>``), not generic ``<div>``s standing in for them.
- A visible focus ring on every interactive element, and
  ``prefers-reduced-motion`` (the browser setting that asks pages to skip
  animations) honoured.
- No custom font loaded at all: text uses the browser's own default fonts
  (``ui-sans-serif`` / ``system-ui`` for prose, Tailwind's ``font-mono``
  stack for the built-command block), so nothing else has to download or
  render before the page is legible.

Usage
-----
::

    # Wrap a Python CLI exposing make_parser() in a single-file GUI
    python scripts/cli_to_gui.py path/to/cli.py:make_parser \\
        --out dist/index.html --title "My Tool"

    # Pipe to stdout for a quick preview
    python scripts/cli_to_gui.py mypkg.cli:build_parser

Refactor note
-------------

The real implementation now lives in the :mod:`sprezzature_cli_gui`
package, next to this file. This module itself is a thin facade: it
re-exports that package's full public API, so both ways of using it, as
``python scripts/cli_to_gui.py`` on the command line and as
``from cli_to_gui import ...`` in Python code, keep working exactly as
before.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import os
import sys

# Put the repo root (the parent of ``scripts/``) on ``sys.path`` so the
# ``sprezzature_cli_gui`` package resolves whether this facade is imported
# or run directly as a script. sys.path[0] would otherwise be ``scripts/``,
# which does not contain the package.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sprezzature_cli_gui.adapters.argparse import (  # noqa: E402
    _action_kind,
    serialize_action,
    walk_parser,
)
from sprezzature_cli_gui.adapters.click import (  # noqa: E402
    _click_param_choices,
    _click_param_kind,
    _serialize_click_param,
    walk_click,
)
from sprezzature_cli_gui.adapters.help_text import (  # noqa: E402
    HELP_TIMEOUT_S,
    RE_ARGPARSE_SUBS,
    RE_CHOICE_HINT,
    RE_COMMAND_LINE,
    RE_COMMANDS_HEADER,
    RE_DEFAULT_HINT,
    RE_OPTION_LINE,
    RE_OPTIONS_HEADER,
    RE_POSITIONAL_HEADER,
    RE_REQUIRED_HINT,
    RE_USAGE_HEADER,
    _extract_prog,
    _parse_commands_section,
    _parse_option_line,
    _parse_options_section,
    _run_help,
    _section,
    walk_from_help,
)
from sprezzature_cli_gui.cli import main  # noqa: E402
from sprezzature_cli_gui.loader import load_parser_from_spec  # noqa: E402
from sprezzature_cli_gui.renderer import (  # noqa: E402
    _children_html,
    _e,
    _field_html,
    _form_html,
    render_html,
)
from sprezzature_cli_gui.schema import (  # noqa: E402
    NO_DEFAULT,
    _safe_default,
    walk,
)

# Re-export the full public API so ``from cli_to_gui import X`` keeps
# resolving for every consumer (tests, docstrings, the entry point).
__all__ = [
    "HELP_TIMEOUT_S",
    "NO_DEFAULT",
    "RE_ARGPARSE_SUBS",
    "RE_CHOICE_HINT",
    "RE_COMMAND_LINE",
    "RE_COMMANDS_HEADER",
    "RE_DEFAULT_HINT",
    "RE_OPTION_LINE",
    "RE_OPTIONS_HEADER",
    "RE_POSITIONAL_HEADER",
    "RE_REQUIRED_HINT",
    "RE_USAGE_HEADER",
    "_action_kind",
    "_children_html",
    "_click_param_choices",
    "_click_param_kind",
    "_e",
    "_extract_prog",
    "_field_html",
    "_form_html",
    "_parse_commands_section",
    "_parse_option_line",
    "_parse_options_section",
    "_run_help",
    "_safe_default",
    "_section",
    "_serialize_click_param",
    "load_parser_from_spec",
    "main",
    "render_html",
    "serialize_action",
    "walk",
    "walk_click",
    "walk_from_help",
    "walk_parser",
]


if __name__ == "__main__":
    raise SystemExit(main())
