# Contributing

## Setup

```sh
git clone https://github.com/warith-harchaoui/sprezzature-cli-gui.git
cd sprezzature-cli-gui
pip install -e ".[dev]"
```

The `-e` flag installs the package in "editable" mode: your local checkout is used directly, so an edit to a `.py` file takes effect the next time you run the code, with no reinstall step. Click, Typer, FastAPI and the MCP (Model Context Protocol, the protocol through which AI agents call tools in English) server are base dependencies, so the full test suite runs with nothing else to install. `[dev]` adds the test toolchain: pytest, ruff, mypy and httpx2. The CI (continuous integration, a server that reruns the tests on every push) workflow (`.github/workflows/ci.yml`) has three jobs: `test` installs `.[dev]` with `requirements-dev.txt`, then runs `ruff check .` and `pytest -q` on Python 3.12; `real-tailwind` runs `pytest -q -m real_tailwind`, where a missing Tailwind CLI (its standalone command-line program, which compiles the page's styles) is a failure rather than a skip; `floor` checks that the package installs and imports on Python 3.10. mypy is not in CI: the pre-push hook (`.githooks/pre-push`, enabled once per clone with `git config core.hooksPath .githooks`) runs `ruff check .`, `mypy sprezzature_cli_gui`, `mypy scripts` and `pytest -q` before every push.

## Run tests

```sh
python -m pytest -q
```

## Lint

```sh
ruff check .
ruff format --check .
```

`ruff check` looks for actual problems (unused imports, undefined names); `ruff format --check` only reports whether the formatting already matches what `ruff format` would produce, without changing anything. Run `ruff format .` (no `--check`) to apply the formatting yourself before committing.

## Style

Follow [CODING.md](CODING.md): NumPy-style docstrings, full type annotations, no filler transitions, no dash used as a sentence aside.

## Adding a fourth framework adapter

Every adapter reduces its framework's parser object to the same shape: `{"prog": str, "description": str, "actions": [...], "sub_commands": {...}}`. To add one:

1. Write `sprezzature_cli_gui/adapters/<framework>.py` with a `walk_<framework>(obj) -> dict` function that produces that shape; look at `adapters/click.py` for the pattern of a framework imported lazily, only when `schema.walk` is handed one of its objects.
2. Wire the new framework's isinstance check into `schema.walk`, imported lazily inside the function body, the same way the argparse and Click checks are.
3. If the framework's parser object is callable, add it to the "already a parser" check in `loader.load_parser_from_spec`, or the loader will call it and run the target tool. Click commands and Typer apps are both on that list for this reason.
4. `renderer.py`, `audit.py` and `cli.py` need no change: they only ever see the shared dict shape.

## Submitting a patch

1. Fork the repository.
2. Create a branch named `feature/<short-description>` for a new capability, or `fix/<short-description>` for a bug fix.
3. Keep each commit atomic: one commit should correspond to one coherent change, not a mix of unrelated edits.
4. Open a pull request against `main`.

Everything the package does installs with `pip install sprezzature-cli-gui`: there have been no feature extras since 2026-11-01. A new dependency goes into the base `dependencies` of `pyproject.toml`, not into an extra; `[dev]` is reserved for the test toolchain.
