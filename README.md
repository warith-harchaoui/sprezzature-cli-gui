# sprezzature-cli-gui

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-cli-gui/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-cli-gui/main/assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

Turn any Python command-line tool into a clickable form, automatically. A command-line
tool takes typed text ("do this, with these options") instead of buttons and fields;
this package reads the tool's own definition of its commands and options and builds a
web page with a button and a field for each one, so a person who has never opened a
terminal can still use it.

Point this tool at a parser: the object inside a Python CLI that reads and validates
the typed command. `argparse` (in Python's standard library), `Click`, and `Typer` are
the three common ways to build one; all three are supported. Given that parser, this
package emits a single self-contained page written in plain JavaScript and styled with
Tailwind (a CSS framework, meaning it ships pre-made style classes instead of hand-
written CSS). Every sub-command becomes a section, every flag a field. The page never
runs the command itself: it assembles the exact command line as text, in the visitor's
own browser, ready to copy and paste, to hand to a desktop app through a `Tauri`
`invoke` call (`Tauri` wraps a web page as a native desktop app; `invoke` is how
that wrapper lets the page call back into it), or to send to a FastAPI endpoint (a small
Python web server) that runs it for real.

For example: a CLI with a `--verbose` flag and a `convert INPUT OUTPUT` sub-command
becomes a page with a checkbox for `--verbose` and two text fields for `INPUT` and
`OUTPUT`; filling them in and pressing "Build command" prints the exact line
`mytool convert in.csv out.json --verbose` for the visitor to copy.

No framework, no build step: the emitted page is one static HTML file. It does load
Tailwind's "Play" build from a CDN (`cdn.tailwindcss.com`) to turn the utility classes
into real CSS in the visitor's browser, so opening the file needs an internet
connection the first time; the form fields themselves still work, unstyled, without one.

## Install

```bash
pip install sprezzature-cli-gui           # core (argparse)
pip install "sprezzature-cli-gui[click]"  # add Click support
pip install "sprezzature-cli-gui[typer]"  # add Typer support
```

## Use

```bash
# From a parser factory in an importable module
sprezzature-cli-gui my_pkg.my_cli:build_parser > gui.html

# From a script path
sprezzature-cli-gui ./my_cli.py:make_parser > gui.html
```

When the parser cannot be imported, the tool falls back to parsing the tool's `--help`
output, so it works even against a CLI it cannot introspect directly.

## How it works

`cli_to_gui.py` is a thin wrapper that re-exports the real implementation, which lives
in the `sprezzature_cli_gui` package:

- `adapters/`: read (introspect, meaning: examine the parser object's own fields
  directly, rather than guess from printed text) an argparse or Click parser; or, when
  no parser object is reachable, fall back to parsing the tool's `--help` text instead.
- `schema.py`: the one normalized command/flag description every adapter produces, so
  the renderer never needs to know which of the three frameworks it came from.
- `renderer.py`: turns that description into the self-contained HTML + Tailwind +
  plain-JavaScript page.
- `loader.py`: resolves a `module:factory` or `path.py:factory` spec (a string naming
  where the parser-building function lives) down to the actual parser object.

## License

BSD-3-Clause © Warith Harchaoui. Part of the [sprezzature](https://harchaoui.org/warith/sprezzature/) toolkit.
