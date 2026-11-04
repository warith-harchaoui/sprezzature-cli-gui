# Coding standards: sprezzature-cli-gui

## Language

Python 3.10 or newer. Every function and class carries full type annotations. Avoid the catch-all type `Any`; where it is truly unavoidable (a parser object that may come from argparse, Click or Typer, for instance), leave a comment saying why.

## Docstrings

NumPy style: a short summary line, then a `Parameters` section and a `Returns` section for anything non-trivial. Every module carries a docstring that names what it does and why it is shaped the way it is; see any file under `sprezzature_cli_gui/` for the expected depth.

## Comments

A comment earns its place by explaining *why* a choice was made (a constraint, a workaround, a non-obvious trade-off), never by restating in English what the line already says in Python. The adapters lean on this heavily: `click = None` inside a bare `except ImportError` reads like a shrug until the comment next to it explains why the isinstance check is kept able to survive Click's absence (see below).

## Style

- `ruff` runs both the linter and the formatter; the line-length limit is 100 characters. Run `ruff format .` before committing rather than hand-fixing whitespace.
- No filler transitions in prose or comments ("Moreover," "Furthermore," "crucial," "game-changer," "delve into"): if a sentence needs one of these to sound weighty, cut the sentence back to what it actually says.
- No em dash or en dash used as a sentence aside. Use a comma, a colon, a semicolon, parentheses, or simply a second sentence instead.

## Tests

`pytest` runs the suite. `tests/test_cli_gui.py` covers the package end to end, through the command-line entry point; `tests/test_units.py` covers the pure functions underneath directly (the schema dispatcher, each adapter, the HTML field renderer, the spec loader). New logic gets a unit test at the level where it actually lives, not only an end-to-end one: a bug in one function's edge case is far cheaper to pin down from a two-line unit test than from a subprocess round-trip.

## Optional imports

Click and Typer are both **base** dependencies. Click became one on 2026-10-25, when the argparse front door was dropped and this tool's own command line was written in Click. Typer, FastAPI, uvicorn and fastapi-mcp followed on 2026-11-01, when every feature extra was folded into the base. An install line asking pip for a `[click]`, `[typer]`, `[api]` or `[mcp]` extra of this package names one that does not exist, and pip warns and carries on rather than failing. A Typer app is read through the Click adapter: `schema.walk` converts it with Typer's own `get_command` and walks the result as Click, so there is no Typer adapter.

Both `schema.walk` and `loader.load_parser_from_spec` still import `click` and `typer` inside a `try`/`except ImportError` at the point of use, never at module scope. That is no longer load-bearing for the base install, since both are always there. It is kept because it costs nothing and keeps the argparse path importable in an environment where one of them has been removed by hand.

## Versioning

Semantic versioning (`major.minor.patch`): a change that breaks the `SPEC` string format, an existing `sprezzature-cli-gui` flag, or the shape of the parser-tree dict that `schema.walk` produces, bumps the minor version, not the patch version.
