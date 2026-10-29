# Landscape

`sprezzature-cli-gui` is the command-line front-end of the [sprezzature](https://sprezzature.ai/) suite, ten Python packages for building publication-quality web content. It reads a command-line tool's own argument parser and writes one static HTML page where every sub-command is a section and every flag is a form field. It adds nothing to the tool it wraps, and it never runs that tool.

## How it fits in the ecosystem

```
sprezzature suite
├── sprezzature-cli-gui        ← this package (a command-line tool becomes a page)
├── sprezzature-ui             (the vanilla JS + Tailwind stack this one emits)
├── sprezzature-accessibility  (20 rules that audit the page afterwards)
├── sprezzature-ux-laws        (30 laws of attention, 8 decidable from the HTML)
├── sprezzature-colors         (contrast, colour-vision deficiency, tokens)
├── sprezzature-figures        (167 chart types, the Ralph Eyeball Loop)
├── sprezzature-maps           (the same numbers attached to real places)
├── sprezzature-publish        (Markdown to a findable site, narration included)
├── sprezzature-audio          (speech to text, text to speech)
└── sprezzature-video          (what a film about a project claims, checked)
```

What comes before: somebody else's command-line tool, written in whatever they wanted, with a parser it already built for itself. What comes after: a host, which is a `Tauri` shell, a FastAPI endpoint, or a shell prompt where the generated line gets pasted. The sister brick is `sprezzature-ui`, which owns the design tokens, the focus-ring conventions and the three-Roboto rule the emitted page obeys; this package is the half of that stack whose input happens to be a parser rather than a drawing. `sprezzature-accessibility` is the natural second pass, because the page this one writes is ordinary HTML and the 20 rules apply to it like any other.

## When to choose it

- A colleague needs a tool you wrote and will not open a terminal, and you are not willing to add a dependency to that tool so they can click it. Nothing here touches the wrapped package: the parser is read in your process, the page comes out, your tool's `pyproject.toml` is unchanged.
- The artefact has to be a file. You want to attach the interface to an issue, drop it on an intranet share, commit it beside the tool, send it by mail. There is no process to keep alive and no port to open.
- The tool is not written in Python. `--from-help` runs the tool's own `--help` in a subprocess and reads the printed text, which covers `cobra` (Go), `clap` (Rust) and `commander` (Node). Measured on this machine: `docker` walked into 57 sub-commands and 1 307 form fields, `gh` into 34 sub-commands, `cargo` into 11 sub-commands and 185 fields.
- You generated a page months ago and the tool has moved since. `sprezzature-cli-gui-audit` compares the committed page against the live parser and exits 1 when a flag became unreachable, when a dropped choice narrowed a dropdown, or when the command line the page builds names a program that does not exist.

## When to pick something else

- **[Trogon](https://github.com/Textualize/trogon), by Textualize.** The most interesting neighbour, and it wins outright when the people you are helping do live in a terminal. Two lines (`@tui()`) make the interface a sub-command of the tool itself, so it is rebuilt from the live parser on every invocation and cannot go stale, which is the guarantee this package has to spend a separate audit command to approximate. It also reads Click's parameter model more completely than anything here does. You pay with a `textual` dependency inside the tool you wrapped, and with an interface that lives in a terminal, which is the room the person you are helping already refused to enter.
- **[Gooey](https://github.com/chriskiehl/Gooey), by Chris KIEHL.** The reference for this whole category, around 21 000 stars, and after a quiet stretch it is being moved forward again in 2026 for Python 3.14 and wxPython 4.3. It does the thing this package deliberately does not: it runs the command, streams the output into a panel, and drives a progress bar off a regular expression you hand it. If what you need is a desktop application that executes, take Gooey and accept wxPython on the machine that runs it.
- **[click-web](https://github.com/fredrik-corneliusson/click-web), by Fredrik CORNELIUSSON.** The closest web competitor. It serves a Click script over Flask, runs the command for real, and streams the output back to the browser. Choose it when execution is the point and a running server is acceptable. Its README is honest that it has only been exercised on basic Click features; variadic file and path arguments, prompts and custom `ParamType`s are out.
- **[Cli2Gui](https://github.com/FHPythonUtils/Cli2Gui).** Reads more parser kinds than anything else in this table: argparse, optparse, docopt, Click and getopt, with Dear PyGui or FreeSimpleGUI underneath, still being released in 2026. If the tool you have to wrap is an old script built on `optparse` or `docopt`, this is the one that already knows how to read it.
- **[Galaxy](https://docs.galaxyproject.org/en/latest/dev/schema.html).** For a laboratory handing analyses to people who are not programmers, Galaxy solved this fifteen years ago: a tool XML describes the form, a command template says how the arguments are assembled, and the platform runs the job, keeps the history and records the provenance. It costs a hand-written wrapper per tool and a platform to operate; it buys an institution.
- **Streamlit, Gradio, NiceGUI, Shiny for Python.** None of them reads a parser. They are the right answer when the interface is the product rather than a face bolted onto an existing command, and when you are willing to write every widget yourself. The tell is simple: if the screen needs state, a chart, a login or a second page, you want one of these and not a generated form.

## Ideas worth stealing

Twenty-five tools were read for this document. Studying a competitor and bringing nothing back is wasted work, so here is what is worth taking, best value first. Two entries are refusals, with the reason, and that is the useful half.

**[click-web](https://github.com/fredrik-corneliusson/click-web): say what you do not support, before the user finds out.** Its README states plainly that variadic file and path arguments, prompts and custom `ParamType`s will not work. Here the degradation is silent: `adapters/click.py:_click_param_kind` falls through to `return "text"` for any `click.ParamType` it does not recognise, and `--from-help` degrades almost everything to text by construction. The work is a sixth rule in `audit.py`, `kind-degraded`, reporting every action whose parser knew more than the field the page offers: a custom `ParamType`, `multiple=True`, `nargs=-1`, an argparse `type=` callable that is neither `int` nor `float`. Cost: an afternoon. The audit half already exists, with five rules and a `Finding` dataclass, so this is one more pattern and one more test in `tests/test_the_page_still_covers_the_cli.py`. Best ratio on this list.

**[Seqera Platform](https://seqera.io/): a launch form remembers the previous run.** Every launch is stored with the exact parameter set that produced it, and the next one starts from one of them. The page this package emits is stateless, so somebody who filled thirty of `docker`'s 1 307 fields loses all of it on a refresh. The work is about twelve lines of JavaScript in `renderer.py`'s `js_payload`: write the form state to `localStorage` keyed on `tree["prog"]` on every `input` event, restore it on load. The question that arrives with it is the useful one, because a page that remembers a `--password` field is a liability: the same change wants a `data-cli-secret` attribute on any action whose `dest` matches `password|token|secret|key`, excluded from the save. Cost: an afternoon, no dependency, and it does not touch `schema.py`, so `audit.py` keeps working unchanged.

**[Cli2Gui](https://github.com/FHPythonUtils/Cli2Gui): publish the per-parser support matrix.** Its documentation says exactly which field kinds each parser recovers: argparse gets Bool, Int, Choice, File and Text; Click gets Bool, Int, Choice and Text; DocOpt gets Bool and Text and nothing else. This package says "lower fidelity" about `--from-help` and never says what is lost. The work is a `confidence` key on every action dict in `schema.py`, set to `"read"` by the two introspecting adapters and to `"guessed"` by `adapters/help_text.py` wherever a kind came from a metavar heuristic rather than from a declared type, then surfaced in `--json` and printed in the emitted page's footer. Cost: half a day. This is an idea the brick already has at half strength, which is usually the best ratio there is: the fallback adapter's own docstring describes the trade-off precisely, and nothing carries it into the output.

**[react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form): a `uiSchema` separate from the data schema.** What a form looks like changes without touching what it means. Control over the rendering is this package's weakest honest score in the table below, and the reason is in one file: `renderer.py` hardcodes the Tailwind token block and every utility class, and the only two levers a caller has are `--title` and `--prog`. The work is `render_html(tree, ui=None)` accepting `{dest: {"widget": "textarea", "order": 3, "group": "Advanced"}}`, with a `--ui ui.json` flag, defaulting to today's output when absent. Cost: a day. It leaves `schema.py` untouched, which is why `audit.py` survives it: the audit reads `data-cli-flag`, not layout.

**[Gooey](https://github.com/chriskiehl/Gooey): stream the output, and drive a progress bar from a regular expression** the author supplies (`progress_regex=r"^progress: (\d+)%$"`). The page here ends at a `<pre id="cli-out">` and a footer telling the reader to wire it up themselves, which is the correct boundary and also a cliff. The work is `--emit-runner {none,sse,tauri}` on `sprezzature-cli-gui`: with `sse` it writes a companion `runner.py` of about forty lines beside the page, a FastAPI endpoint that runs the built line and streams stdout, plus the `<pre id="cli-log">` block and the `EventSource` wiring in the HTML. Cost: a day. The dependency lands in the generated project and never in the wrapped tool, so the headline guarantee survives; the care is in the quoting, and `renderer.py` already has a conservative shell quoter to reuse.

**[Trogon](https://github.com/Textualize/trogon): make the interface a sub-command of the tool**, so there is no artefact to keep in sync at all; `mytool tui` rebuilds the UI from the live parser every time. The version here is a `gui_command()` helper exported from `sprezzature_cli_gui`, which a Click or Typer author registers with `app.add_command(gui_command())` to get `mytool gui`, writing the page to a temporary file and opening a browser. Cost: half a day of code, and a real argument against it. It reverses the one property no other row in the table has, which is that nothing is added to the wrapped tool. Take it only as an opt-in documented as such, never as the recommended path, or the package stops being the thing it is.

**[nf-core launch](https://nf-co.re/docs/nf-core-tools/cli/pipelines/launch): hand over a parameter file, not a command line. Refused as a default.** It writes the filled form to `nf-params.json` and tells the user to run `nextflow run … -params-file nf-params.json`. A parameter file survives copy-paste, goes into a repository and gets reviewed; a 1 307-field command line does not. The version here would be a "Download params" twin of the "Build command" button, fifteen lines of JavaScript. It is refused as a default because of a fact about the targets rather than about the work: argparse's `fromfile_prefix_chars` is off unless the tool's author turned it on, Click has no equivalent, and a page that offers a parameter file to a tool that cannot read one is a worse lie than no button at all. It belongs behind an explicit `--params-file` flag, used by somebody who knows their tool accepts it.

**[Galaxy](https://docs.galaxyproject.org/en/latest/dev/schema.html): separate the form from the command assembly. Refused.** A Cheetah template in `<command>` lets one visible field expand into three flags, lets a conditional suppress an argument, and frees the shape the user sees from the shape the tool takes. It is genuinely better than one-field-to-one-flag. It is refused as a direction rather than on budget: a template layer is a second description of the tool, maintained by hand and free to drift from the parser, and preventing exactly that drift is why `audit.py` exists and why `data-cli-flag` carries an exact string rather than a label. Galaxy can afford it because a community of curators maintains those wrappers. One author cannot keep `docker`'s 1 307 fields' worth of templates true, and a stale template is indistinguishable from a correct one until somebody runs it.

## How the field divides

The first split is between **reading the parser** and **asking the author to describe the tool again**. One family reaches into the tool and reads the object it already built for itself: this package, Trogon, Gooey, Cli2Gui, click-web, quick, argparseui. Nothing is restated, so nothing can disagree. The other family wants a second description: Galaxy's tool XML, nf-core's `nextflow_schema.json`, a JSON Schema fed to react-jsonschema-form, a Streamlit script written widget by widget. The second family buys expressiveness, because a hand-written description can say things a parser cannot, and it pays with drift, because two descriptions of one tool are two things to keep true.

The second split is **a file against a process**. Almost everything in this table is a program that must be running while somebody uses the interface: a Flask server, a wxPython window, a Textual application, a Streamlit script, a Galaxy instance. That is what makes execution possible, and it is also what makes the interface something to deploy and to operate. The static corner is small: this package, trogon_js, a built react-jsonschema-form page, React code emitted by v0. A file can be committed, attached, mirrored and opened offline; it also cannot run anything, which is not a limitation to work around but the trade being made. The map below finds this split on its own and puts it on the vertical axis.

The third split is about **what the tool is for**. Streamlit, Gradio, NiceGUI, Shiny for Python, Taipy, PyWebIO, Flet, Dear PyGui and Textual are in this table because people reach for them the moment somebody says "my colleague will not type this command", and they are almost always the expensive answer to that sentence. None of them reads a parser, and all of them ask you to write the interface. They earn their place when the screen has become a product in its own right, with state, several pages and users who never heard of the command underneath. The 2026 arrivals sit at the same place from the other side: v0, Lovable and bolt.new will write you a beautiful form from a paragraph of prose, and nothing in that chain ever reads the parser, so the form is as right as the prose was and no mechanism exists to keep it right next month.

## How it compares

Every alternative is rated 1 to 5 on each criterion, higher is better (⭐ weak to ⭐⭐⭐⭐⭐ strongest). The scores are an argued judgement from reading the projects, not a benchmark, and every axis is oriented so that more stars mean stronger on that trait, including cost, where more stars mean cheaper or more open. A `⭐` means the tool does not do what the criterion measures, which on a capability scale is a 1 and not a blank. The machine-readable source is [`assets/landscape.csv`](assets/landscape.csv), generated from the table below: 25 tools across 14 criteria.

| Tool | Zero setup in the wrapped tool | Static hostable output | No dependency added to the target | Parser frameworks read automatically | Non-Python command-line tools | Fidelity of what is read | Runs the wrapped command | Live log streaming | Control over the rendering | Accessibility of the produced form | Interface guaranteed to match the tool | Lightness of the install | Free and self-hostable | Maturity and ecosystem |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| sprezzature-cli-gui | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| Gooey | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Trogon | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| trogon_js | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| click-web | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Cli2Gui | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| quick (Qt5 for Click) | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| argparseui | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| Streamlit | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Gradio | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| NiceGUI | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Shiny for Python | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Taipy | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| PyWebIO | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Flet | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Dear PyGui | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Textual | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| react-jsonschema-form | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Galaxy | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| nf-core launch | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Seqera Platform | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| v0 (Vercel) | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| Lovable | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| FastAPI + Swagger UI | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Typer's own `--help` | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

Three columns name a property rather than a familiar word. **Zero setup in the wrapped tool** scores how much the target's author must do (add a decorator, restructure the application, write a second description) before an interface exists at all. **Interface guaranteed to match the tool** scores whether the interface can go stale: a runtime generator rebuilds it from the live parser on every run and scores 5, a hand-written form scores 1, and this package scores 4 because the artefact is static but a separate audit command checks it. **Lightness of the install** scores what has to arrive on the machine beside the generator, from nothing extra to a whole platform.

![Positioning map of 25 tools for putting an interface on a command-line tool, on two axes derived from a principal component analysis. sprezzature-cli-gui sits alone in the top-right corner, with v0 level with it on the far left of the same top edge and react-jsonschema-form just below. The opposite corner, bottom left, holds the application frameworks packed together: NiceGUI, Dear PyGui, Flet, Streamlit, Gradio, Taipy and Textual, none of which reads a parser. Along the bottom edge sit the tools that run the command they wrap: Gooey at the very bottom, with Cli2Gui, Trogon, quick and click-web beside it. Typer's own --help is at the far right, low down. The horizontal axis opposes tools that need nothing from the tool they wrap to tools that give you control over the rendering; the vertical axis opposes a finished portable file against a program that executes while somebody watches.](assets/landscape.svg)

The source is [`assets/landscape.csv`](assets/landscape.csv), the star table above and nothing added, and the map is regenerated with:

```sh
standpoint assets/landscape.csv --outdir assets --stem landscape --check
```

The geometry is ordinary correlation PCA and is **deterministic**: the same table gives the same map every run, whatever model named the poles. The four words at the edges come from a local model, and they are vaguer than the loadings behind them, so here is what the two axes are actually made of.

**Horizontal, `Precision` on the left and `Seamless` on the right.** Zero setup in the wrapped tool (+0.44), interface guaranteed to match the tool (+0.39), fidelity of what is read (+0.38) and parser frameworks read automatically (+0.32) pull right; control over the rendering (−0.34), non-Python command-line tools (−0.23) and maturity and ecosystem (−0.23) pull left. It is the axis that separates *reading a tool* from *drawing an interface*, and the left pole is where the money is: the tools over there cost more setup and give you more say in what comes out. `sprezzature-cli-gui` sits at the far right by construction, because it is the reference row and `standpoint` anchors the reference top-right.

**Vertical, `Versatile` at the bottom and `Portable` at the top.** Static hostable output (+0.44), accessibility of the produced form (+0.37), non-Python command-line tools (+0.29) and no dependency added to the target (+0.29) pull up; runs the wrapped command (−0.44), live log streaming (−0.34), interface guaranteed to match the tool (−0.23) and free and self-hostable (−0.21) pull down. The bottom pole is a single coherent thing, *a program that executes while somebody watches*, and the top is its absence, a finished artefact. Gooey is at the very bottom with Trogon and Cli2Gui beside it; this package and v0 share the top edge. That is the map noticing that "hands you a form" and "runs your job" are different businesses. Note that one criterion loads on both axes with opposite signs: the interfaces that cannot go stale are the ones rebuilt at run time, which are also the ones that run the command.

**Two axes carry 56.1 % of the table** (32.0 % and 24.1 %). That is the number to hold onto: nearly half of what those 14 criteria say is *not* on this page. The map is a first orientation and the table is the evidence. `standpoint --check` also reports `readable: False` on this figure, and the reason is honest rather than cosmetic: seven of the application frameworks score almost identically on all 14 criteria, so they land on top of each other near the bottom-left corner. That pile-up is the finding. `standpoint` writes a prose interpretation beside the figure too; it is not reproduced here, because a model reading back ratings somebody wrote is not a finding, and this file is more useful if the judgements stay visibly mine.

## Sources

- [Trogon, by Textualize](https://github.com/Textualize/trogon), and [trogon_js](https://github.com/johnhw/trogon_js), the JavaScript variant of the same idea
- [Gooey](https://github.com/chriskiehl/Gooey) and [its 2026 maintenance plan](https://github.com/chriskiehl/Gooey/issues/974)
- [click-web](https://github.com/fredrik-corneliusson/click-web)
- [Cli2Gui](https://github.com/FHPythonUtils/Cli2Gui)
- [quick, a Qt5 GUI generator for Click](https://github.com/szsdk/quick), and [argparseui](https://github.com/mtav/argparseui)
- [The Galaxy tool XML reference](https://docs.galaxyproject.org/en/latest/dev/schema.html)
- [nf-core launch](https://nf-co.re/docs/nf-core-tools/cli/pipelines/launch)
- [react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form)
- [Streamlit, Gradio and NiceGUI compared, 2026](https://www.pistack.xyz/posts/2026-08-29-python-ui-frameworks-streamlit-gradio-nicegui-comparison/)
- [Which Python GUI library should you use in 2026](https://www.pythonguis.com/faq/which-python-gui-library/)
