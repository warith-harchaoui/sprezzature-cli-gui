# Changelog: sprezzature-cli-gui

## Unreleased

### Fixed

- `adapters/help_text.py`, `_parse_options_section`: a help entry wrapped onto more than one indented continuation line only kept the first line; every line after that was silently dropped. Continuation lines now accumulate and are joined before the option is emitted.

### Changed

- Removed every em-dash-as-aside from `sprezzature_cli_gui/*.py` docstrings and comments per WRITING.md, and ran `ruff format` across the package.
- Corrected two documentation claims that no longer matched the emitted HTML: README.md said the generated page makes "no network call at runtime", when it in fact loads Tailwind's Play build from a CDN; `scripts/cli_to_gui.py`'s docstring described a Roboto-typeface fallback that the renderer's CSS never implements.

### Added

- `tests/test_units.py`: unit tests for the pure functions behind the package (`schema.walk` dispatch, both adapters, the help-text fallback parser, the HTML field renderer, `loader.load_parser_from_spec`), on top of the existing end-to-end suite in `tests/test_cli_gui.py`.
- LISEZMOI.md, CODING.md, CONTRIBUTING.md, EXAMPLES.md, LANDSCAPE.md/PAYSAGE.md, TRIGGERS.md, Dockerfile, requirements\*.txt, and the `references/` pointer files, matching the structure already in place for sibling `sprezzature-*` packages.

## v1.0.0 (2026-07-29)

Initial standalone release, extracted from the `sprezzature` monorepo.

### Package

- `sprezzature_cli_gui/loader.py`: resolves a `module:factory` or `path.py:factory` spec down to a parser object.
- `sprezzature_cli_gui/schema.py`: the shared parser-tree shape and the `walk()` dispatcher.
- `sprezzature_cli_gui/adapters/`: one adapter per supported framework (argparse, Click and, through Click, Typer) plus the `--from-help` fallback that works on any CLI, Python or not.
- `sprezzature_cli_gui/renderer.py`: turns the parser tree into a single self-contained HTML page.
- `sprezzature_cli_gui/cli.py`: the `sprezzature-cli-gui` command-line entry point.
- `scripts/cli_to_gui.py`: a thin facade re-exporting the package's public API, kept for anyone already scripting against the pre-split single-file layout.
