# sprezzature-cli-gui

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[![logo](assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

Auto-generate a single-file HTML GUI from any Python command-line tool. Point it at an
argparse, Click, or Typer parser and it emits a vanilla-JavaScript + Tailwind page that
maps every sub-command and flag to a form field. The page builds the command string
locally in the browser, ready to copy, to hand to a Tauri `invoke`, or to drive a
FastAPI endpoint.

No framework, no build step, no network at runtime: the emitted page is one static file.

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

`cli_to_gui.py` is a thin facade over the `sprezzature_cli_gui` package:

- `adapters/` — introspect an argparse / Click parser, or parse `--help` text.
- `schema.py` — the normalized command/flag schema every adapter produces.
- `renderer.py` — schema → a self-contained HTML + Tailwind + vanilla-JS page.
- `loader.py` — resolve a `module:factory` or `path.py:factory` spec to a parser.

## License

BSD-3-Clause © Warith Harchaoui. Part of the [sprezzature](https://harchaoui.org/warith/sprezzature/) toolkit.
