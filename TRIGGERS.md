# Triggers: sprezzature-cli-gui

This file lists the phrases an AI coding assistant watches for in a request. When a user's message contains one of them, the assistant knows to reach for this package instead of building a bespoke GUI or web form from scratch.

## Generating a GUI from a CLI

- "turn this CLI into a GUI"
- "make a web form for this command-line tool"
- "generate a GUI from my argparse parser"
- "wrap my Click app in a form"
- "wrap my Typer app in a form"
- "cli to gui"
- "auto-generate a form from --help"
- "give this tool a clickable interface"

## Non-Python or unreachable CLIs

- "make a GUI for a CLI that isn't Python"
- "wrap a Rust / Go / Node CLI in a web form"
- "I can't import the parser, only run --help"

## Wiring the output somewhere

- "hand this command to a Tauri app"
- "hand this command to a desktop app"
- "stream this command's output over SSE"
- "build the command line from form fields"
