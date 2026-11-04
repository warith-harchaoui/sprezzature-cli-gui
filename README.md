# sprezzature-cli-gui

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/logo.png)](https://sprezzature.ai/)

Turn a command-line tool into a clickable form, automatically. A command-line
tool takes typed text ("do this, with these options") instead of buttons and fields;
this package reads the tool's own definition of its commands and options and builds a
web page with a field for each one, so a person who has never opened a terminal can
still use it.

Point it at a parser: the object inside a Python CLI (command-line interface) that
reads and validates the typed command. `argparse` (in Python's standard library),
`Click` and `Typer` are the three common ways to build one; all three are imported and
walked directly. A CLI written in anything else, such as Go's `cobra` or Rust's `clap`,
is covered by `--from-help`, which runs the tool's own `--help` in a subprocess and
reads the text. That works on any CLI at all, at lower fidelity: help text says less
than a parser knows.

From that parser, the package emits a single self-contained page written in plain
JavaScript and styled with Tailwind (a CSS framework that ships pre-made style classes
instead of hand-written CSS). Every sub-command becomes a collapsible section with its
own form, and every flag a field. The page never runs the command. It assembles the
exact command line as text, in the visitor's own browser, ready to copy and paste, to
hand to a desktop app through a `Tauri` `invoke` call (`Tauri` wraps a web page as a
native desktop app; `invoke` is how that wrapper lets the page call back into it), or
to send to a server that runs it.

For example: a CLI with a `convert INPUT OUTPUT` sub-command that also takes
`--verbose` becomes a page with a `convert` section holding two text fields and a
checkbox. Filling them in and pressing "Build command" prints the exact line
`mytool convert in.csv out.json --verbose` for the visitor to copy.

No framework, no build step: the emitted page is one static HTML file. It does load
Tailwind's "Play" build from a CDN (content delivery network, here
`cdn.tailwindcss.com`) to turn the utility classes into real CSS in the visitor's
browser, so the styling needs an internet connection. The form fields and the
"Build command" button still work, unstyled, without one.

## How it works

![Flow diagram. At the top, a command-line tool feeds two lanes, which are two ways of reading it. The left lane imports the module and walks the parser object's own fields, at high fidelity. The right lane runs the tool's own help in a subprocess and reads the printed text, at lower fidelity and saying so. Both meet in one outcome, a single normalised description that the renderer turns into one self-contained HTML page.](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/how-it-works.svg)

## Install

```bash
pip install sprezzature-cli-gui
```

One install brings everything: the argparse, Click and Typer readers, the
`--from-help` reader, the audit, the HTTP API and the MCP server. There is no feature
extra. The only extra, `[dev]`, is the test toolchain (pytest, ruff, mypy, httpx2).

## Five surfaces

| Surface | Entry point | What it does |
|---|---|---|
| Library | `from sprezzature_cli_gui import walk, render_html, audit` | Walk a parser in your process, render the page, check a page against a parser. |
| CLI | `sprezzature-cli-gui`, `sprezzature-cli-gui-audit` | The same two jobs from a shell. Both are Click commands. |
| HTTP API | `uvicorn sprezzature_cli_gui.api:app`, or `docker compose up` | FastAPI routes: a schema tree in, the page out; a page and a tree in, the findings out. |
| MCP | `sprezzature-cli-gui-mcp` | The same routes as MCP (Model Context Protocol) tools for an agent host. |
| Skill | `sprezzature-cli-gui` in the [sprezzature hub](https://github.com/warith-harchaoui/sprezzature/tree/main/sprezzature-cli-gui) | The `SKILL.md` an agent such as Claude Code reads to know when to route here. |

The CLI and the library import your module. The HTTP API and the MCP server never do:
they take the schema tree that `walk` produces, not a `module:factory` spec. Importing
an arbitrary module named by an unauthenticated caller would be remote code execution,
so that step stays on your machine.

## Command line

### `sprezzature-cli-gui`: a parser in, a page out

```bash
# From a parser factory in an importable module
sprezzature-cli-gui my_pkg.my_cli:build_parser > gui.html

# From a script path, written to a file with a page title
sprezzature-cli-gui ./my_cli.py:make_parser --out gui.html --title "My Tool"

# From a CLI that cannot be imported, or is not Python at all
sprezzature-cli-gui --from-help "mytool" --out gui.html
```

`SPEC` is `module:factory` or `path/to/file.py:factory`. The name after the colon is a
zero-argument function that returns an `argparse.ArgumentParser`, a `click.Command` or
a `typer.Typer`. It can also name such an object directly: the loader then uses it as
is and never calls it, because calling a Click command or a Typer app runs it.

| Option | Effect |
|---|---|
| `--from-help` | Treat `SPEC` as a shell command line, run it with `--help` appended, and parse the printed text. Nothing falls back to this on its own: pass it explicitly. |
| `--out PATH` | Write the HTML to `PATH` instead of stdout. |
| `--title TEXT` | The page `<title>`. Defaults to the program name. |
| `--prog TEXT` | Override the program name in the page and in the built command line. The name a Click group or a Typer app reports (a function name, or `cli` for a multi-command Typer app) is rarely the installed command name. |
| `--json` | Print the walked parser tree as JSON instead of HTML. |
| `--version`, `-h`/`--help` | Version and help. |

A spec that cannot be found, imported or walked exits with status 1 and one sentence on
stderr.

Shell completion comes from Click:

```bash
eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=bash_source sprezzature-cli-gui)"   # bash
eval "$(_SPREZZATURE_CLI_GUI_COMPLETE=zsh_source sprezzature-cli-gui)"    # zsh
```

### `sprezzature-cli-gui-audit`: does the page still cover the CLI?

A page generated last month can fall behind a CLI that has moved since. The audit takes
the same `SPEC` and the page, and reports five kinds of disagreement:

| Rule | Meaning |
|---|---|
| `flag-not-in-page` | An option the parser accepts has no field in the page. |
| `field-has-no-flag` | A field builds an option the parser does not accept. |
| `choice-dropped` | A choice the parser offers is missing from the page's dropdown. |
| `prog-missing` | The page does not seed its command line with a program name. |
| `prog-mismatch` | The page builds a command line for a different program name. |

```bash
sprezzature-cli-gui-audit mytool.cli:build_parser gui.html
sprezzature-cli-gui-audit mytool.cli:build_parser gui.html --format json --prog mytool
```

It exits 0 when the page covers the CLI and 1 when there is at least one finding. A
`PAGE` that is not a file also exits 1, with a message. `--prog` has the same meaning
as for the generator; `--format` is `text` (default) or `json`.

## Library

```python
from sprezzature_cli_gui import walk, render_html, audit

tree = walk(build_parser())               # argparse, Click or Typer, in your process
html = render_html(tree, title="My Tool")
open("gui.html", "w", encoding="utf-8").write(html)

for finding in audit(tree, html):         # an empty list means the page covers the CLI
    print(finding.rule, finding.subject, finding.message)
```

`walk(obj, prog=None)` returns the canonical tree: `prog`, `description`, `actions`,
`sub_commands`. It raises `TypeError` for anything that is not one of the three parser
types. `render_html(tree, title="CLI GUI")` returns the complete page.
`audit(tree, page)` returns a list of `Finding` objects (`rule`, `subject`, `message`).

## HTTP API

```bash
uvicorn sprezzature_cli_gui.api:app --host 0.0.0.0 --port 8000
```

| Method and path | `operation_id` | What it does |
|---|---|---|
| `GET /health` | `health` | Liveness probe: `{"status": "ok"}`. |
| `GET /v1/example` | `get_example_schema` | A schema tree walked from a small demo parser, to copy the shape from. |
| `POST /v1/render` | `render_gui` | Body `{"tree": ..., "title": ...}`; returns the page as HTML. Answers 400 when the tree lacks `prog` or `actions`. |
| `POST /v1/audit` | `audit_gui` | Body `{"schema": ..., "page": ...}`; returns `{"findings_total": n, "findings": [...]}`. |

Interactive documentation is served at `/docs` and `/redoc`.

With Docker, `docker compose up -d` builds the image and serves these routes on port
8000. The compose file mounts `./work` at `/work` and sets `PYTHONPATH=/work`, so the
command line inside the container can import a CLI you put there:

```bash
docker compose run --rm api sprezzature-cli-gui mytool.cli:build_parser --out /work/gui.html
```

The image's default command is `sprezzature-cli-gui-mcp --host 0.0.0.0 --port 8000`,
so one container serves the HTTP routes and the MCP endpoint at `/mcp` on the same port.

## MCP server

```bash
sprezzature-cli-gui-mcp                       # 127.0.0.1:8000
sprezzature-cli-gui-mcp --host 0.0.0.0 --port 9000
```

It serves the same FastAPI app with an MCP endpoint mounted at `/mcp`, over HTTP. The
defaults come from `SPREZZATURE_CLI_GUI_HOST` and `SPREZZATURE_CLI_GUI_PORT` when they
are set. Each tool name is the route's `operation_id`: `health`, `get_example_schema`,
`render_gui`, `audit_gui`. Agent routing is described in
[TRIGGERS.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/TRIGGERS.md).

## What the page contains

- A root form for the top-level options, then one collapsible `<details>` section per
  sub-command, nested as deep as the parser goes.
- A field per option: a checkbox for a boolean flag, a dropdown for a choice list, a
  number input for an integer or a float, and a text input for everything else. File
  arguments are text inputs with a `path/to/file` placeholder; a real file picker
  belongs to the host.
- A "Build command" button in each form. It builds the command line from that form's
  fields only, so a top-level flag does not appear in a sub-command's line.
- A `<pre id="cli-out">` block where the built line appears, with conservative shell
  quoting.

Every field carries a `data-cli-flag` attribute naming the option it builds, which is
what the audit reads. Wiring examples for Tauri and Server-Sent Events are in
[EXAMPLES.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/EXAMPLES.md).

## Inside the package

- `adapters/`: one reader per source. `argparse.py` and `click.py` walk a live parser
  object; a Typer app is converted to its Click command and walked as Click.
  `help_text.py` parses printed `--help` text.
- `schema.py`: `walk`, the dispatcher that reduces every source to the same tree.
- `renderer.py`: `render_html`, the tree to the self-contained page.
- `loader.py`: resolves a `module:factory` or `path.py:factory` spec to the parser.
- `audit.py`: the five rules above.
- `cli.py`, `audit_cli.py`, `_generate.py`: the two Click commands and the work behind
  the generator.
- `api.py`, `mcp.py`: the HTTP and MCP surfaces.

`scripts/cli_to_gui.py` re-exports the package for use from a clone.

## Development

```bash
pip install -e ".[dev]"
ruff check .
python -m pytest -q
```

See
[CONTRIBUTING.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/CONTRIBUTING.md)
and, for the neighbours of this package,
[LANDSCAPE.md](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/LANDSCAPE.md).

## License

BSD-3-Clause © Warith HARCHAOUI. Part of the [sprezzature](https://sprezzature.ai/) toolkit.
