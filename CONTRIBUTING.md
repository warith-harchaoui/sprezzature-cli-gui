# Contributing

## Setup

```sh
git clone https://github.com/warith-harchaoui/sprezzature-cli-gui.git
cd sprezzature-cli-gui
pip install -e ".[dev,click,typer]"
```

The `-e` flag installs the package in "editable" mode: your local checkout is used directly, so an edit to a `.py` file takes effect the next time you run the code, with no reinstall step. The `click` and `typer` extras are pulled in too so the full test suite (both adapters) runs locally, matching what `.github/workflows/ci.yml` installs.

## Run tests

```sh
pytest
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

1. Write `sprezzature_cli_gui/adapters/<framework>.py` with a `walk_<framework>(obj) -> dict` function that produces that shape; look at `adapters/click.py` for the pattern of a framework whose import stays optional.
2. Wire the new framework's isinstance check into `schema.walk`, imported lazily inside the function body, the same way the existing two are.
3. `renderer.py` and `cli.py` need no change: they only ever see the shared dict shape.

## Submitting a patch

1. Fork the repository.
2. Create a branch named `feature/<short-description>` for a new capability, or `fix/<short-description>` for a bug fix.
3. Keep each commit atomic: one commit should correspond to one coherent change, not a mix of unrelated edits.
4. Open a pull request against `main`.

Click and Typer stay optional extras, not requirements. Any new adapter or feature that touches them must still let the base install (`pip install sprezzature-cli-gui`, no extras) import cleanly and serve the argparse path.
