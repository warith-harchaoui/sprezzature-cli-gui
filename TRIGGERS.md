# Triggers: sprezzature-cli-gui

When someone needs a face on a command-line tool, or wants to know whether an existing
face still matches the tool, and what to call.

This file is written for an agent: a Claude Code skill, an MCP (Model Context Protocol)
host, anything choosing a tool on someone's behalf. Humans are welcome, but the routing
rules below are the point.

---

## The generalisation, stated once

> **Route here when the request is about a command-line tool and a form for it.** The
> domain has a closed vocabulary, and a request belongs here when it pairs one word
> from each list:
>
> - **the tool**: CLI, command line, command-line tool, script, parser, argparse,
>   Click, Typer, `--help`, flags, options, sub-commands, arguments, cobra, clap;
> - **the face**: GUI, form, web form, interface, page, UI, fields, "fill in", "click".
>
> A third word turns a making request into a checking one: **still, stale, drift,
> out of date, missing flag, covers, matches, audit** about a page already generated.

The pairing is the mechanism, not any particular phrasing. "My colleague keeps getting
the flags wrong", « il faudrait une interface pour que l'équipe puisse lancer ce
script », "can the ops team use this without a terminal" all name the tool and the
face, and all route here.

The instinct this file exists to interrupt is hand-writing a bespoke form, or reaching
for a framework, when the tool's own parser already describes every control the page
needs.

Not this one when there is no command-line tool behind the screen (`sprezzature-ui`),
when the page exists and the question is its accessibility (`sprezzature-accessibility`),
or when the job is to run the command and stream its output: this package only builds
the command line.

---

## Every tool, and the request it answers

| Tool | Surface | The request it answers |
|---|---|---|
| `sprezzature-cli-gui SPEC` | CLI | "Make a form for this Python CLI": imports `module:factory` and walks the argparse, Click or Typer parser. |
| `sprezzature-cli-gui --from-help "CMD"` | CLI | "Make a form for this CLI I cannot import" (Go, Rust, Node, a binary): parses `CMD --help`. |
| `sprezzature-cli-gui SPEC --json` | CLI | "Show me what was read from this parser": the schema tree, without HTML. |
| `sprezzature-cli-gui-audit SPEC PAGE` | CLI | "Does this generated page still cover the CLI?": five rules, exit 1 on any finding. |
| `walk`, `render_html`, `audit` | Library | The same three jobs from Python, in the caller's process. |
| `health` | MCP / HTTP `GET /health` | "Is the server up?" Only for diagnosing a connection. |
| `get_example_schema` | MCP / HTTP `GET /v1/example` | "What does a schema tree look like?" Call it before `render_gui` when the shape is unknown. |
| `render_gui` | MCP / HTTP `POST /v1/render` | "Turn this schema tree into a page." Tree in, one self-contained HTML page out. |
| `audit_gui` | MCP / HTTP `POST /v1/audit` | "Does this page still match this schema tree?" Returns `findings_total` and the findings. |

---

## What to call, on every surface

| Job | Library | CLI | MCP tool (= `operation_id`) |
|---|---|---|---|
| Read a Python parser and emit a page | `walk` + `render_html` | `sprezzature-cli-gui SPEC` | *(none: it imports the user's module)* |
| Read `--help` text and emit a page | `adapters.help_text.walk_from_help` + `render_html` | `sprezzature-cli-gui --from-help "CMD"` | *(none: it runs the user's command)* |
| Schema tree to page | `render_html` | none | `render_gui` |
| See the schema shape | `walk` | `sprezzature-cli-gui SPEC --json` | `get_example_schema` |
| Check a page against its parser | `audit` | `sprezzature-cli-gui-audit SPEC PAGE` | `audit_gui` |
| Liveness | none | none | `health` |

The gap is deliberate. Reading a parser means importing the user's code, and reading
`--help` means running it. Both belong on the user's machine, not behind an HTTP
request. The HTTP and MCP surfaces take the schema tree instead.

The MCP tools are served by `sprezzature-cli-gui-mcp` (endpoint `/mcp`). The skill
named `sprezzature-cli-gui` lives in the sprezzature hub and points at the same tools.

---

## Two contracts an agent must not break

**1. `render_gui` takes a schema tree, not source code.** It will not read a Python
file and work out the argparse calls. Either run the CLI, which introspects the real
parser, or describe the sub-commands and flags in the shape `get_example_schema`
returns. A tree without `prog` or `actions` is refused with a 400.

**2. The page builds a command line; it does not run one.** Nothing here executes the
user's CLI, which is why it can be an ordinary HTTP tool at all. Wiring the built
command to something that runs it (a Tauri shell, a Server-Sent Events log stream, a
job runner) is the caller's job, and the place to be careful.

---

## Phrasings, for matching

Examples of the pairing above, not a list to match against.

**Making the form**: "turn this CLI into a GUI", "web form for this command-line
tool", "generate a GUI from my argparse parser", "wrap my Click / Typer app in a form",
"auto-generate a form from --help", « une interface web pour mon script », « un
formulaire pour cette commande ».

**Not a Python CLI**: "make a GUI for a CLI that isn't Python", "wrap a Rust / Go /
Node CLI in a web form", "I can't import the parser, only run --help".

**Checking the form**: "is this generated page still up to date with the CLI", "the
form is missing a flag", "did the GUI drift from the tool", « la page couvre-t-elle
encore toutes les options ».
