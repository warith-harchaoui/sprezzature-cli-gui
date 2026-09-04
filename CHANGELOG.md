# Changelog: sprezzature-cli-gui

## Unreleased

### Fixed

- `adapters/help_text.py`, `_parse_options_section`: a help entry wrapped onto more than one indented continuation line only kept the first line; every line after that was silently dropped. Continuation lines now accumulate and are joined before the option is emitted.
- `loader.py`, `load_parser_from_spec`: pointing the spec directly at an already-built `click.Command`/`Group` (instead of a zero-argument factory function) called it, which runs the target CLI for real (a `click.Command` is itself callable). The loader now detects an already-built `argparse.ArgumentParser` or `click.Command` and uses it as is.
- `cli.py`: `--help`'s own usage line named the parser `sprezzature-cli-gui-to-html`, which is not the installed console script (`sprezzature-cli-gui`). Also dropped a description clause pointing at `assets/examples/cli-gui-demo/`, a path that does not exist in this repo.
- `renderer.py`: the emitted page used sprezzature-ui semantic Tailwind classes (`bg-brand-blue`, `text-label-primary`, `border-separator`, ...) without ever shipping the `tailwind.config` block that defines them, so on the plain Tailwind Play CDN every one of those classes compiled to nothing; the page's one call-to-action button rendered invisible (white text on a transparent background) while still being clickable. Found by generating a GUI from a real CLI and opening it in a browser, not by the test suite. Fixed by injecting the token-defining `tailwind.config` script. Also removed a `dark:border-separator-dark` reference to a token never defined anywhere.
- `schema.py`/`cli.py`: the "Build command" output named the wrapped function (e.g. `main`, a Click group's decorated function name) instead of the installed console-script name, producing a command that does not exist. Added a `--prog` flag threaded through `schema.walk()` so callers can supply the real program name.
- `adapters/help_text.py`, the `--from-help` fallback: verified against real non-Python CLIs (clap's `cargo`, cobra's `gh` and `docker`), not just synthetic help text, and found four real gaps in that verification pass:
  - A clap-style repeatable flag (`-v, --verbose...`) leaked its trailing ellipsis into both the flag and the generated dest, producing an unrunnable `--verbose...` on the built command line.
  - A clap-style `<CODE>` metavar kept its closing `>` (`"CODE>"` instead of `"CODE"`), because only the leading bracket was stripped.
  - clap prints its one-line synopsis *before* `Usage:`, not after (unlike argparse/Click); the parser only ever looked after the usage block, so `cargo --help` produced a description made of the second, unrelated `Usage:` continuation line instead of the real "Rust's package manager" synopsis.
  - cobra's own CLIs favor bare, colon-less, often qualified section headers (`USAGE` with the command on the next line, `FLAGS`, `Global Options`, `Common Commands`, `GITHUB ACTIONS COMMANDS`) and colon-suffixed sub-command names (`auth:`). None of that matched the option/command/usage header patterns, which assumed a trailing colon and the bare keyword alone: `gh --help` parsed to an empty tree (no description, no options, no sub-commands) and `docker --help` lost its global flags entirely and folded three unrelated command-group listings into its description. Headers now tolerate an optional colon, an optional qualifier prefix, and (for `Usage`) a synopsis living on the following line; every matching command-group header is now merged instead of just the first.

### Changed

- Removed every em-dash-as-aside from `sprezzature_cli_gui/*.py` docstrings and comments per WRITING.md, and ran `ruff format` across the package.
- Corrected two documentation claims that no longer matched the emitted HTML: README.md said the generated page makes "no network call at runtime", when it in fact loads Tailwind's Play build from a CDN; `scripts/cli_to_gui.py`'s docstring described a Roboto-typeface fallback that the renderer's CSS never implements.

### Added

- `tests/test_units.py`: unit tests for the pure functions behind the package (`schema.walk` dispatch, both adapters, the help-text fallback parser, the HTML field renderer, `loader.load_parser_from_spec`), on top of the existing end-to-end suite in `tests/test_cli_gui.py`, plus regression tests for every `--from-help` fix listed above.
- LISEZMOI.md, CODING.md, CONTRIBUTING.md, EXAMPLES.md, LANDSCAPE.md/PAYSAGE.md, TRIGGERS.md, Dockerfile, requirements\*.txt, and the `references/` pointer files, matching the structure already in place for sibling `sprezzature-*` packages.
- `tests/test_cli_gui.py::test_installed_console_script_actually_resolves`: runs the installed `sprezzature-cli-gui` console script directly. Every other CLI-level test in the suite drove the legacy, unpackaged `scripts/cli_to_gui.py` facade instead, so a typo in `pyproject.toml`'s `[project.scripts]` entry would have passed CI (setuptools does not import the target at install time) and only broken the moment a real user typed the command.

## v1.0.0 (2026-07-29)

Initial standalone release, extracted from the `sprezzature` monorepo.

### Package

- `sprezzature_cli_gui/loader.py`: resolves a `module:factory` or `path.py:factory` spec down to a parser object.
- `sprezzature_cli_gui/schema.py`: the shared parser-tree shape and the `walk()` dispatcher.
- `sprezzature_cli_gui/adapters/`: one adapter per supported framework (argparse, Click and, through Click, Typer) plus the `--from-help` fallback that works on any CLI, Python or not.
- `sprezzature_cli_gui/renderer.py`: turns the parser tree into a single self-contained HTML page.
- `sprezzature_cli_gui/cli.py`: the `sprezzature-cli-gui` command-line entry point.
- `scripts/cli_to_gui.py`: a thin facade re-exporting the package's public API, kept for anyone already scripting against the pre-split single-file layout.
