# Landscape: sprezzature-cli-gui in context

The table below scores six tools for turning a command-line tool into something a non-terminal user can operate, one star column per axis. A star rating runs from 1 (weak) to 5 (excellent); a cell marked `--` means the tool does not attempt that axis at all, so scoring it would be meaningless.

| Tool | Zero-config | Static output | Multi-framework | No new dependency in the target app | Non-Python CLIs |
|---|---|---|---|---|---|
| **sprezzature-cli-gui** | **5** | **5** | **4** | **5** | **3** |
| Streamlit | 2 | -- | -- | 1 | -- |
| Gradio | 2 | -- | -- | 1 | -- |
| Gooey | 3 | -- | 2 | 2 | -- |
| PySimpleGUI | 2 | -- | 1 | 2 | -- |
| Typer's own `--help` | 5 | -- | -- | 5 | -- |
| click-web | 3 | 2 | 1 | 2 | -- |

Three columns name a property rather than a familiar word: **Zero-config** scores how much setup the target CLI's author has to do (decorate every option again, restructure the app, add a server) before a GUI appears at all. **Static output** scores whether the result is a plain file that can be hosted anywhere, versus a process that has to keep running. **No new dependency in the target app** scores whether using the tool pulls a runtime dependency into the CLI being wrapped, or stays entirely on the generating side.

## Notes

**Streamlit** and **Gradio** build a full interactive web app, with live execution, not just a form: far more capable when the goal is a real running tool, but they ask the CLI's author to rewrite the interaction as Streamlit/Gradio widgets. The result is a Python process that must keep running, not a file to hand off.

**Gooey** decorates an existing argparse script and pops up a desktop window built with wxPython; closer in spirit to sprezzature-cli-gui, but it requires wxPython installed on the machine that runs the GUI and does not export anything static.

**PySimpleGUI** is a general desktop-GUI toolkit; nothing about it is specific to wrapping a CLI; using it to wrap one means hand-building every field yourself.

**Typer's own `--help`** is not a competitor so much as the reason a "no new dependency" column matters: Typer already gives excellent terminal ergonomics for free, but it never produces a form a non-terminal user can click through.

**click-web** is the closest existing tool: it also reads a Click app's own structure and serves a web form for it, but it runs as a live Flask server (so "static output" scores low) and, unlike sprezzature-cli-gui's `--from-help` fallback, has no path for a CLI it cannot import directly.

## Where sprezzature-cli-gui fits

Its distinguishing feature is emitting a **single static HTML file** from a CLI's own parser object, with no server to keep running and no change required to the CLI itself: point it at an existing `argparse`, Click, or Typer parser (or, at lower fidelity, at any CLI's `--help` text, Python or not) and get back a file that assembles the exact command line as text, ready to hand to whatever actually runs it.
