# cli-gui-demo — runbook

This file is named `RUNBOOK.md` (not `README.md`) on purpose: the
Anthropic skill spec forbids `README.md` anywhere inside a skill
folder. The skill's `SKILL.md`, and the package's `README.md` and
`LISEZMOI.md`, cover the overview; this runbook covers how to launch and
read the demo.

Worked example of the **sprezzature-cli-gui** skill's flagship CLI (command-line interface, a program driven by typing a line in a terminal) → GUI (graphical user interface, windows, buttons and fields you click) workflow. A mock CLI (`imgconvert`) is wrapped in a single-page GUI built with vanilla JavaScript, Tailwind CSS (Cascading Style Sheets, the rules that set a page's colours, fonts and spacing), the Roboto family (sans / serif / mono), and a tiny Python proxy.

## What it shows

The CLI is small but exercises every flag-to-control mapping in the skill's CLI → GUI recipe:

| CLI flag shape | GUI control |
|---|---|
| Positional path | `<input type="text">` |
| `int` | `<input type="number">` |
| Bounded `int` (e.g. `--quality 1-100`) | `<input type="range">` + live `<output>` |
| 3-option `enum` (`--to {png,jpg,webp}`) | `<fieldset role="radiogroup">` styled as segmented control |
| `boolean` (`--keep-aspect`) | `<input type="checkbox" role="switch">` styled as a pill |
| Streaming stdout | `<pre>` log panel with auto-scroll, fed by Server-Sent Events |

See `manifest.json` for a per-file map of which skill principle each piece demonstrates.

## Launch

```bash
cd "$(sprezzature-cli-gui-skill --path)/assets/examples/cli-gui-demo"
python server.py
```

Open <http://localhost:8787>. No `pip install` is needed; the server uses only the Python standard library, and the GUI uses the Tailwind Play CDN (no build step). The three Roboto families are bundled under `public/fonts/roboto/`, `public/fonts/roboto-serif/`, and `public/fonts/roboto-mono/` and served by the same proxy.

## How it maps to the skill's CLI → GUI workflow

The eight steps from `SKILL.md` → "CLI → GUI workflow":

1. **Inventory the CLI** — read `cli/imgconvert.py` (or `python cli/imgconvert.py --help`). Three subcommands: `resize`, `convert`, `optimize`.
2. **Categorize each command** — all three are form-driven with a streamed log. None are list-producing.
3. **Pick a layout** — 3 commands → sidebar on the start (desktop) and a horizontal tab strip (mobile). See `public/index.html` `<nav id="sidebar">`.
4. **Map flags to form controls** — see the table above.
5. **Wire execution** — `public/app.js` posts JSON (JavaScript Object Notation, a text format of named fields) to `/run` on the Python proxy; `server.py` spawns the CLI and streams stdout back via Server-Sent Events.
6. **Stream output** — `app.js` consumes the SSE (Server-Sent Events) stream and appends each line to the `<pre>` log panel.
7. **Emit a single page** — one HTML, one JavaScript module, one CSS (Tailwind directives via the Play CDN, the content delivery network that serves Tailwind as a script), Roboto / Roboto Serif / Roboto Mono self-hosted.
8. **Document launch** — this file.

## File structure

```text
cli-gui-demo/
├── RUNBOOK.md                      this file
├── manifest.json                   principles each file demonstrates
├── server.py                       HTTP + SSE proxy (Python stdlib only)
├── cli/
│   └── imgconvert.py               mock CLI (3 subcommands)
└── public/
    ├── index.html                  GUI markup
    ├── app.js                      vanilla ES module
    ├── favicon.svg                 single-shape SVG icon
    └── fonts/
        ├── roboto/                 variable + italic-variable WOFF2 + OFL.txt (sans)
        ├── roboto-serif/           variable + italic-variable WOFF2 + OFL.txt (serif)
        └── roboto-mono/            variable + italic-variable WOFF2 + OFL.txt (mono)
```

Total lines (excluding fonts and this file): ~1,070.

## What's not here

- **Real image conversion** — the CLI writes a stub file. Adding Pillow would distract from the GUI-mapping demo.
- **Authentication, persistence, multi-step wizards** — not relevant to this demo.
- **A bundled Tailwind build** — the Play CDN keeps the demo zero-build. For production, `references/stack-tailwind.md` in the `sprezzature-ui` skill documents the Tailwind CLI / Vite swap.
- **WCAG (Web Content Accessibility Guidelines) audit** — `sprezzature-accessibility-lint "$(sprezzature-cli-gui-skill --path)/assets/examples/cli-gui-demo/public/"` should pass; this demo is meant to be a clean baseline.

## License

The demo is released under the BSD (Berkeley Software Distribution, a permissive licence: keep the copyright notice and do what you like) 3-Clause licence (see `LICENSE` at the root of the `sprezzature-cli-gui` repository). The Roboto, Roboto Serif, and Roboto Mono families retain their SIL (Summer Institute of Linguistics, the body that wrote it) Open Font License; see the `OFL.txt` bundled in each `public/fonts/roboto*/` folder.
