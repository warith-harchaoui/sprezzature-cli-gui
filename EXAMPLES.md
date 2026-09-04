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
pip install "sprezzature-cli-gui[click]"
sprezzature-cli-gui mypkg.cli:cli --out gui.html
# cli here can be the click.Group / click.Command object itself (mypkg/cli.py
# defines `cli = click.group()(...)` at module level): the loader detects an
# already-built Click object and uses it as is. It never calls it directly,
# since a click.Command is itself callable and calling one runs it for real.
```

## A Typer app

```sh
pip install "sprezzature-cli-gui[typer]"
```

```python
# mypkg/cli.py
import typer

app = typer.Typer()


@app.command()
def greet(name: str = "world"):
    print(f"Hello {name}")


def get_click_group():
    # Typer builds a Click group internally and exposes it as app.cli; the
    # spec's factory name cannot itself be a dotted path ("app.cli" is not
    # a single attribute), so a one-line wrapper hands that group back.
    return app.cli
```

```sh
sprezzature-cli-gui mypkg.cli:get_click_group --out gui.html
```

## A CLI whose factory cannot be imported, or that is not Python at all

```sh
sprezzature-cli-gui --from-help "mytool --some-global-flag" --out gui.html
# Runs `mytool --some-global-flag --help` as a subprocess and parses the
# printed text instead of a live parser object. Works on Rust (clap), Go
# (cobra), Node (commander) CLIs too, at lower fidelity than native
# introspection: every option becomes a plain text field unless the help
# line spells out a [default: …], a set of choices, or a recognised METAVAR.
```

## Inspecting the parser tree without rendering HTML

```sh
sprezzature-cli-gui mypkg.cli:build_parser --json | python -m json.tool
# Useful when debugging why a flag rendered as the wrong field kind, or when
# piping the tree into a different renderer (a Tauri app's own template, say).
```

## Wiring the emitted page to something that actually runs the command

The generated page never executes anything; it only assembles the command line as
text into a `<pre id="cli-out">` block. Three common ways to take it from there:

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
