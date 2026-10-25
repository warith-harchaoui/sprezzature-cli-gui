#!/usr/bin/env python3
"""
``sprezzature-cli-gui`` — a command-line tool in, a single-page web GUI out.

One front door. There were two until 2026-10-25: an argparse one that did the
work, and a click one that rebuilt an argument vector and called it — a wrapper
around a parser around the work, so every option existed three times and a flag
added to one could be missing from the other. The work moved to
:mod:`sprezzature_cli_gui._generate`, and this calls it directly.

Click is the only parser now, and a base dependency rather than an extra: with
argparse gone nothing ships with Python that can parse a command line, so an
optional click would mean an install whose own command does not run.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from sprezzature_cli_gui._generate import GenerationError, build_tree, render, write

#: Shown under the options. Completion is click's, and nobody finds it by
#: guessing.
_EPILOG = """\
Shell completion:

  \b
  eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=bash_source sprezzature-cli-gui)"   # bash
  eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=zsh_source sprezzature-cli-gui)"    # zsh

Examples:

  \b
  sprezzature-cli-gui mytool.cli:build_parser --out gui.html
  sprezzature-cli-gui --from-help 'ffmpeg -h' --out ffmpeg.html
"""


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=_EPILOG,
    help=(
        "Introspect a Python CLI (argparse OR Click, autodetected) and emit a "
        "self-contained single-page GUI for it. SPEC is module:factory, or a "
        "shell command line with --from-help."
    ),
)
@click.version_option(package_name="sprezzature-cli-gui")
@click.argument("spec")
@click.option(
    "--from-help",
    "from_help",
    is_flag=True,
    default=False,
    help=(
        "Treat SPEC as a shell command line and parse its --help output. "
        "Works on non-Python CLIs; lower fidelity than introspection."
    ),
)
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    default=None,
    help="Write the HTML here instead of stdout.",
)
@click.option("--title", default=None, help="Page <title>.")
@click.option(
    "--prog",
    default=None,
    help=(
        "Override the program name in the page and the built command line. A "
        "Click group's name defaults to the decorated function's name, not the "
        "installed console script — pass the real one when they differ, or the "
        "page names a command that does not exist."
    ),
)
@click.option(
    "--json",
    "json_",
    is_flag=True,
    default=False,
    help="Emit the walked parser as JSON instead of HTML.",
)
def main(
    spec: str,
    from_help: bool,
    out: Path | None,
    title: str | None,
    prog: str | None,
    json_: bool,
) -> None:
    """Walk SPEC and write its GUI."""
    try:
        tree = build_tree(spec, from_help=from_help, prog=prog)
        output = render(tree, as_json=json_, title=title)
        written = write(output, out)
    except GenerationError as exc:
        # One sentence and stop. The four exception types the two front doors
        # used to catch separately all mean the same thing to the person who
        # typed the command: the spec did not work.
        raise SystemExit(f"cli_to_gui: {exc}") from exc

    if written is None:
        sys.stdout.write(output)
    else:
        # stderr, so `--out -` style piping and shell redirection stay clean.
        print(f"cli_to_gui: wrote {written}", file=sys.stderr)


if __name__ == "__main__":
    main()
