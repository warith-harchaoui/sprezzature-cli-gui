# Examples: sprezzature-cli-gui

Each block below is a complete, runnable command followed by what it writes to disk or prints to the terminal. Read [README.md](README.md) first for what the tool does in one line; this file is for copying a working invocation rather than reading a full explanation.

## An argparse CLI, piped to stdout

```sh
sprezzature-cli-gui path/to/cli.py:make_parser > gui.html
# make_parser() takes no arguments and returns an argparse.ArgumentParser
```

## An argparse CLI with sub-commands, written to a file

```sh
sprezzature-cli-gui mypkg.cli:build_parser --out dist/index.html --title "My Tool"
# Every sub-command the parser registers via add_subparsers() becomes its own
# collapsible <details> section in the page, each with its own "Build command" button.
```

## A Click app

```sh
sprezzature-cli-gui mypkg.cli:cli --out gui.html
# cli here can be the click.Group / click.Command object itself (mypkg/cli.py
# defines `cli = click.group()(...)` at module level): the loader detects an
# already-built Click object and uses it as is. It never calls it directly,
# since a click.Command is itself callable and calling one runs it for real.
```

## A Typer app

```python
# mypkg/cli.py
import typer

app = typer.Typer()


@app.command()
def greet(name: str = "world"):
    print(f"Hello {name}")
```

```sh
sprezzature-cli-gui mypkg.cli:app --prog mytool --out gui.html
# The spec names the Typer app itself. The loader recognises a typer.Typer and
# never calls it (calling one runs the app); walk() converts it to its Click
# command and reads it as Click. --prog matters here: a single-command Typer
# app is named after its function ("greet"), not after the installed command.
```

## A CLI whose factory cannot be imported, or that is not Python at all

```sh
sprezzature-cli-gui --from-help "mytool --some-global-flag" --out gui.html
# Runs `mytool --some-global-flag --help` as a subprocess and parses the
# printed text instead of a live parser object. Works on Rust (clap), Go
# (cobra), Node (commander) CLIs too, at lower fidelity than native
# introspection: an option with no value placeholder becomes a checkbox, and
# one with a placeholder a plain text field, unless the help line spells out
# a set of choices or a recognised METAVAR (INT, FLOAT, PATH, FILE...); a
# [default: …] in the help line pre-fills the field.
```

## Inspecting the parser tree without rendering HTML

```sh
sprezzature-cli-gui mypkg.cli:build_parser --json | python -m json.tool
# Useful when debugging why a flag rendered as the wrong field kind, or when
# piping the tree into a different renderer (a Tauri app's own template, say).
```

## Wiring the emitted page to something that actually runs the command

The generated page never executes anything; it only assembles the command line as
text into a `<pre id="cli-out">` block. Two common ways to take it from there:

```js
// Tauri desktop app: read the built command from the page and run it locally.
import { invoke } from "@tauri-apps/api/core";
const commandLine = document.getElementById("cli-out").textContent;
await invoke("run_shell_command", { commandLine });
```

```js
// FastAPI backend over Server-Sent Events: stream the command's output back.
const es = new EventSource(`/run?cmd=${encodeURIComponent(commandLine)}`);
es.onmessage = (e) => console.log(e.data);
```

## Checking a page committed earlier

```sh
sprezzature-cli-gui-audit mypkg.cli:build_parser dist/index.html
# Prints one line per finding, then exits 1; prints "The page covers the CLI."
# and exits 0 when nothing has drifted. --format json gives
# {"findings_total": n, "findings": [{"rule", "subject", "message"}, ...]}.
```

## The HTTP API, with a tree walked locally

```sh
uvicorn sprezzature_cli_gui.api:app --port 8000 &
curl -s localhost:8000/v1/example                    # the shape to copy
sprezzature-cli-gui mypkg.cli:build_parser --json > tree.json
python -c "import json; print(json.dumps({'tree': json.load(open('tree.json')), 'title': 'My Tool'}))" \
  | curl -s -X POST localhost:8000/v1/render -H 'content-type: application/json' -d @- > gui.html
# The server takes the tree, never a module:factory spec: importing a module
# named by a remote caller would be remote code execution.
```
