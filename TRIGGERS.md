# Triggers: sprezzature-cli-gui

When someone needs a face on a command-line tool, and what to call.

This file is written for an agent — a Claude Code / OpenCode skill, an MCP
host, anything choosing a tool on someone's behalf. Humans are welcome, but
the routing rules below are the point.

---

## The generalisation, stated once

> **The trigger is "somebody who will not type this command needs to run
> it."** That is the whole shape, and it is usually said without the words
> "GUI" or "form": "my colleague keeps getting the flags wrong", "can
> non-technical people use this", "I want a page where you fill in the
> options and hit go", « il faudrait une interface pour que l'équipe puisse
> s'en servir », "make this usable by the ops team". All of it routes here.

The instinct it exists to interrupt is hand-writing a bespoke form, or
reaching for a framework, when the command's own `--help` already describes
every control the page needs.

| The user has… | Route | Why |
|---|---|---|
| a Python CLI you can import (argparse / Click / Typer) | `sprezzature-cli-gui` CLI, pointed at the module | It introspects the real parser, so the form cannot drift from the flags. |
| a CLI you cannot import — Go, Rust, Node, a binary, only `--help` | `sprezzature-cli-gui` on the help text, or build the tree by hand | The schema is the interface; where it came from does not matter. |
| a schema tree already, or a non-Python caller | `render_gui` (MCP / HTTP) | Tree in, one self-contained HTML page out. |
| no idea what a schema tree looks like | `get_example_schema` first | A worked example beats guessing and getting a 422. |

---

## What to call, on every surface

| Job | CLI | MCP tool |
|---|---|---|
| Read a real Python parser and emit a page | `sprezzature-cli-gui` | *(not an MCP tool — it imports the user's module)* |
| Schema tree → HTML page | — | `render_gui` |
| See the schema shape | — | `get_example_schema` |

The gap is the honest one: introspecting a parser means importing the user's
code, which belongs on their machine and not behind an HTTP request on
someone else's.

---

## Two contracts an agent must not break

**1. `render_gui` takes a schema tree, not source code.** It will not read a
Python file and work out the argparse calls for you. Either run the CLI,
which introspects the real parser, or describe the sub-commands and flags in
the shape `get_example_schema` returns.

**2. The page builds a command line; it does not run one.** Nothing here
executes the user's CLI — that is why it can be an ordinary HTTP tool at all.
Wiring the built command to something that runs it (a Tauri shell, an SSE log
stream, a job runner) is the caller's job, and the place to be careful.

---

## Phrasings, for matching

Not a closed list — the generalisation above is the mechanism.

**Making the GUI** — "turn this CLI into a GUI", "web form for this
command-line tool", "generate a GUI from my argparse parser", "wrap my Click
/ Typer app in a form", "cli to gui", "auto-generate a form from --help",
"give this tool a clickable interface", « une interface web pour mon
script », « un formulaire pour cette commande ».

**Not a Python CLI** — "make a GUI for a CLI that isn't Python", "wrap a Rust
/ Go / Node CLI in a web form", "I can't import the parser, only run --help".

**Wiring it up** — "hand this command to a Tauri app", "stream this command's
output over SSE", "build the command line from form fields".
