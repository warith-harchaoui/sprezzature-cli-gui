# Changelog

## [Unreleased]

### Changed

- The `brand-blue` and `brand-red` tokens of the generated page, and the
  demo, follow the corporate palette of
  [deraison.ai/colors](https://deraison.ai/colors/), the source of truth
  for every colour in the suite: `#0088FF` and `#FF383C` (were `#007AFF`
  and `#FF3B30`), dark `#0091FF` and `#FF4245`. The "how it works" diagram
  is redrawn in the same colours.

## [1.7.0] — 2026-11-12

### Added

- The skill an agent reads now ships inside the package, in
  `sprezzature_cli_gui/skill/` (`SKILL.md`, `references/`, the worked demo in
  `assets/examples/cli-gui-demo/`). Until now it lived only in the
  `sprezzature` hub, so `pip install sprezzature-cli-gui` gave four of the
  five surfaces (library, command line, HTTP (HyperText Transfer Protocol, the
  request-and-reply exchange of the web) API (Application Programming
  Interface, the addresses another program calls) and MCP (Model Context Protocol, the protocol through
  which AI agents call tools in English) server) and nothing an agent could
  read. `sprezzature-cli-gui-skill` reports whether the copy under
  `~/.claude/skills` is in step; `--install` copies it there (`--agent
  opencode` for `~/.opencode/skills`), moving a previous copy to
  `skills-superseded/`; `--path` prints the folder, which
  `sprezzature_cli_gui.skill_path()` also returns.

### Fixed

- A Typer 0.29 app raised `AttributeError` when walked: Typer now carries its
  own copy of Click and describes an option's type with `type_descriptor`
  rather than `.type`. The adapter maps that descriptor back to Click's type
  names; checked with Typer 0.20 and 0.29.1.

### Docs

- `README.md`, `LISEZMOI.md` and `TRIGGERS.md` placed the skill in the hub; they now
  document `sprezzature-cli-gui-skill`, `skill_path()` and the `skill/`
  folder. `EXAMPLES.md` gained a skill example.
- The skill's demo runbook told the reader to `cd
  sprezzature-cli-gui/assets/examples/cli-gui-demo`, a path that exists in
  no install; it now uses `sprezzature-cli-gui-skill --path`. It also listed
  a `README.md` the folder does not have and counted ~700 lines for ~1,070.
- `CONTRIBUTING.md` said the continuous-integration workflow runs mypy; it runs
  ruff and pytest, the `real-tailwind` job and the Python 3.10 install
  check, and mypy runs in the pre-push hook.
- `LANDSCAPE.md` and `PAYSAGE.md` said `sprezzature-figures` has 167 chart types; it
  has 168.

## [1.6.0] — 2026-11-08

### Changed

- A generated page no longer loads Tailwind from `cdn.tailwindcss.com`. On
  each run the generator asks the CDN which release is current (one request
  per process), takes that release in full (its standalone CLI, downloaded
  once into `~/.cache/sprezzature-cli-gui/tailwind/` or
  `SPREZZATURE_CLI_GUI_CACHE`) and compiles only the utilities the page uses
  into its `<style>`: about 10 kB, and the page loads nothing.
  `render_html(..., extra_content=[...])` names classes a caller's script adds
  later. Without a network, the newest cached release is used; `--offline`
  (`render_html(..., offline=True)`, `SPREZZATURE_CLI_GUI_OFFLINE=1`) asks for
  that. An empty cache is an error naming the cache and the cause;
  `POST /v1/render` answers 503. A server that answers with an error
  (`HTTP 504` and the URL) is reported apart from an absent network.
  `sprezzature_cli_gui.tailwind`;
  `tests/test_the_page_loads_nothing_from_a_cdn.py`, and
  `tests/test_the_real_tailwind_compiles_the_page.py` for the real binary
  (the `real-tailwind` CI job, where a missing binary fails).
- The Docker image downloads and tries the Tailwind CLI when it is built, so a
  fresh container does not fetch 45 MB on its first page.

### Fixed

- `sprezzature-cli-gui-audit` printed a traceback on a bad SPEC; it now says
  one sentence like the generator. On both commands, a target that raises at
  import or in its factory is one sentence too. `--from-help` refuses an
  unbalanced quote, a `--help` that never answers, and a command that prints
  nothing (it used to write an empty page).
- The MCP server announced its description as its version
  (`serverInfo.version`): fastapi-mcp 0.4 passes the description into
  `Server`'s version slot. It now announces the package version, and the
  description goes to `instructions`.
- `--from-help` ignored `--prog`: the page kept the name the help text gave.
- `POST /v1/render` answered 500 on a tree whose `prog` and `actions` were
  present but malformed (an action `{"foo": 1}`); it now answers 400.

## [1.5.2] — 2026-11-05

### Fixed

- `sprezzature-cli-gui` prefixed its error and its "wrote" message with
  `cli_to_gui:`, the script's name before the package existed. Both now say
  `sprezzature-cli-gui:`, the command that was typed.

### Docs

- The README figure called the parser path "tried first" and `--from-help`
  "the fallback", as if one fell back to the other; nothing does, the
  `--from-help` lane is asked for explicitly. Text changed, figure redrawn.
- The `scripts/cli_to_gui.py` docstring said `--from-help` turns every
  option into a text field (an option with no placeholder becomes a
  checkbox), left Typer out of the factory's return types, and described a
  sticky header the page does not have.
- CODING.md placed the guarded `click = None` import in the adapters; it is
  in `schema.walk` and the loader.
- The skill said the package reads `--help` as the source of truth, for
  argparse in particular; it walks argparse, Click and Typer parser objects
  and reads `--help` only under `--from-help`.

## [1.5.1] — 2026-11-05

### Changed

- `sprezzature-cli-gui -V` prints the version, like `--version` and like every
  other brick's front door.

## [1.5.0] — 2026-11-05

### Fixed

- An argparse `store_false` flag (`--no-cache`) rendered pre-ticked, so the
  untouched form built `--no-cache` and turned the option off. A lone flag's
  checkbox now starts unticked and is labelled after the flag; the untouched
  form builds the parser's default invocation.
- A counter (`action="count"`, Click's `count=True`) built `-v 3`, which both
  parsers reject. It is now the `count` kind and repeats the flag: `-v -v -v`.
- A Click `--color/--no-color` pair, and argparse's `BooleanOptionalAction`,
  could never build the off spelling. The action dict gains `off_flags`; the
  checkbox starts at the default and writes the other spelling when changed.
- The program name was pasted raw into the page's script, so a quote ended
  the string and a `</script>` ended the script. It is now a JSON literal with
  `<`, `>` and `&` escaped. The audit reads that form and still reads the
  single-quoted seed of pages generated by 1.4.0 and earlier.
- The command line is built by `addParts`, a function over plain field
  objects, which `tests/test_the_built_command_means_what_the_parser_means.py`
  runs under node and parses back with the real parser.

### Docs

- LANDSCAPE and PAYSAGE said the emitted page obeys the three-Roboto rule; it
  loads no font and uses the system stack (`ui-sans-serif, system-ui`).
- EXAMPLES said `--from-help` turns every option into a text field; an option
  with no value placeholder becomes a checkbox.
- The page footer named `scripts/cli_to_gui.py` as its generator; it now says
  `sprezzature-cli-gui`.
- Docstrings and comments that still called Click optional (the Click adapter,
  `adapters/__init__.py`, the loader, `schema.walk`), the loader's `Returns`
  and `Raises` (argparse only, two exceptions missing), and the CI workflow and
  pyproject comments that named the removed `api` and `mcp` extras.

## [1.4.0] — 2026-11-04: the documentation says what the code does, and the image serves /mcp

### Changed

- `sprezzature-cli-gui-mcp` parses its command line with click instead of
  argparse, like the two other commands. `--host`, `--port`, their
  `SPREZZATURE_CLI_GUI_HOST` / `SPREZZATURE_CLI_GUI_PORT` defaults and exit
  code 2 on a usage error are unchanged; `--version` is new. `main(argv)`
  now returns an `int`. The package's own command lines no longer import
  argparse; only the code that reads a user's argparse parser does.
- The unused `sprezzature_cli_gui/_argparse.py` helper is gone.
- Docker: the image and `docker compose up` run `sprezzature-cli-gui-mcp`
  on 0.0.0.0:8000 instead of `uvicorn sprezzature_cli_gui.api:app`, so one
  container answers both `/v1/...` and `/mcp`. Before, the container had no
  `/mcp`, because the endpoint is mounted when `mcp.py` is imported.
- A guard test runs every console script with `--help` and checks a click
  usage line, and checks that no module of the package imports argparse
  outside the parser readers.

### Docs

The documents now say what the code does, checked against the code and the
installed commands.

- README and LISEZMOI: the install section showed a second `pip install` line
  "to add Typer support", for an extra that no longer exists; Typer is in the
  base. They claimed the tool falls back to `--help` parsing on its own when a
  parser cannot be imported; it does not, `--from-help` has to be passed. The
  example put a top-level `--verbose` in a sub-command's built line; each form
  builds from its own fields only. Added what was missing: the five surfaces,
  every option of `sprezzature-cli-gui`, the `sprezzature-cli-gui-audit`
  command and its five rules, the library (`walk`, `render_html`, `audit`), the
  four HTTP routes with their `operation_id`, Docker and compose, the MCP
  server and its `/mcp` endpoint, and what the emitted page contains.
- TRIGGERS: `audit_gui`, `health` and `sprezzature-cli-gui-audit` were missing
  from the routing tables. The generalisation now routes on the domain's
  vocabulary rather than on phrasings.
- EXAMPLES: the Typer recipe wrapped `app.cli`, which does not exist on Typer;
  the spec now names the Typer app directly. It also asked for a Typer extra.
  "Three common ways" introduced two examples. Added an audit example and an
  HTTP example.
- CONTRIBUTING and CODING: both still called Typer an optional extra. The
  adapter recipe now names the loader's "already a parser" check.
- Docstrings and one help string: `mcp.py` listed three colour tools from
  another brick (`check_contrast`, `simulate_color_blindness`, `get_palette`)
  as this server's tools; `api.py` said sub-commands become tabs and file
  arguments become pickers (they become collapsible sections and text fields)
  and left `/v1/audit` out of its route list; `adapters/click.py` and
  `scripts/cli_to_gui.py` pointed Typer users at `app.cli`; the
  `sprezzature-cli-gui --help` text left Typer out. Its epilog example
  `--from-help 'ffmpeg -h'` ran `ffmpeg -h --help`, since `--from-help`
  appends `--help` itself; it is now `--from-help ffmpeg`.
- Stale comments and messages about the removed extras: the Dockerfile (an
  `api` extra), `requirements.txt` ("Base runtime: none"), the loader's error
  ("install the matching extra"), and a pyproject comment for a Click twin
  entry point that no longer exists. The audit command's comment promised exit
  2 for a missing page; it exits 1, and the comment now says so.
- Removed `requirements-click.txt` and `requirements-typer.txt`: nothing read
  them, and both described Click and Typer as things to install separately.

## [1.3.0] — 2026-11-01: one `pip install`

### Changed — one `pip install`

**Everything this package does now installs with it.** 4 extras became
**one**, and it is not a feature: `[dev]` is the test toolchain.

  Typer (the richer command line) and both surfaces. The base was **one**
  dependency.

Measured across the suite before touching anything: **59 extras over eleven
repositories**, and **six bricks whose base was a single dependency** — so
`pip install <brick>` installed almost nothing and did almost nothing, and
choosing the right extra was a thing a reader had to know *before* the package
could do its job. Here the base goes from **1** to **6**
dependencies.

All eleven unions were dry-run resolved in a clean venv before any manifest was
edited, so this is a measured feasibility and not an optimistic one.

### Fixed — the places that encoded the extras

Install lines, error messages, docstrings, the `Dockerfile`, the CI workflow and
the README/LISEZMOI install sections all named extras that no longer exist. pip
treats an unknown extra as a **warning and exits 0**, so none of these would
have failed loudly: they would have quietly installed nothing.

The hub's `test_no_document_promises_an_extra_that_does_not_exist` found the
cross-repository ones — a document in one brick naming another brick's extra —
which no per-repository pass would have caught.

## [1.2.0] — 2026-10-19

The refusal finally points at something.

This package's best decision is that `POST /v1/render` takes a schema tree and
**refuses** a `module:factory` spec: importing an arbitrary module named by an
unauthenticated caller is remote code execution, and no allow-list makes it
safe enough to be worth it. The refusal sends the caller to the library —
"introspect your own parser, in your own process, with `walk(parser)`".

That was sound advice pointing at nothing. `import sprezzature_cli_gui`
exported a version string.

### Added

- **A library surface**: `walk`, `render_html`, `audit`, `Finding`. The split
  between the first two *is* the security boundary — `walk` imports your
  module and calls your factory, `render_html` does not — so they are the
  package's first-class interface rather than an implementation detail. A test
  runs exactly the round trip the API's refusal describes, and another checks
  it needs no extra: the caller is being asked to run this inside their own
  process, beside their own CLI, and a library that dragged click and typer in
  would be a bigger ask than the thing it replaces.
- **`sprezzature-cli-gui-click`**, the Click twin. There is a joke in shipping
  it, and that is the point: a tool whose job is reading Click commands did
  not offer one. Both front doors build the same namespace and call the same
  handler — checked on the **output**, not on the flag lists, because two
  parsers can declare the same options and disagree about what one means.
  Guarded, so a bare install answers which extra to add rather than a
  traceback about a package the reader never asked for.

The package now holds all ten columns of the suite's surface audit.

 sprezzature-cli-gui

## v1.1.0 (2026-10-02): a backlog of fixes, and the half of the dependency guard nobody runs

### Fixed

- **`mcp.py` defined `main` twice, and the two took different arguments.** One
  definition sits in the `except ImportError` branch reached when the `[mcp]`
  extra is absent, the other in the `else` branch that serves the real
  endpoint. A single console script reaches both, so to a caller they are one
  function. They were not: the fallback took nothing while the real one took
  `argv`, so `main(["--host", "127.0.0.1"])` answered on a machine with the
  extra and raised `TypeError` on a machine without it. The broken half is the
  one a reader who skipped the extra meets first.
- **The declared homepage named a host that no longer answers.**
  `project.urls` pointed at `harchaoui.org`, now returning 503, and PyPI prints
  that link on the package page. It points at `sprezzature.ai`.
- `adapters/help_text.py`, `_parse_options_section`: a help entry wrapped onto more than one indented continuation line only kept the first line; every line after that was silently dropped. Continuation lines now accumulate and are joined before the option is emitted.
- `loader.py`, `load_parser_from_spec`: pointing the spec directly at an already-built `click.Command`/`Group` (instead of a zero-argument factory function) called it, which runs the target CLI for real (a `click.Command` is itself callable). The loader now detects an already-built `argparse.ArgumentParser` or `click.Command` and uses it as is.
- `cli.py`: `--help`'s own usage line named the parser `sprezzature-cli-gui-to-html`, which is not the installed console script (`sprezzature-cli-gui`). Also dropped a description clause pointing at `assets/examples/cli-gui-demo/`, a path that does not exist in this repo.
- `renderer.py`: the emitted page used sprezzature-ui semantic Tailwind classes (`bg-brand-blue`, `text-label-primary`, `border-separator`, ...) without ever shipping the `tailwind.config` block that defines them, so on the plain Tailwind Play CDN every one of those classes compiled to nothing; the page's one call-to-action button rendered invisible (white text on a transparent background) while still being clickable. Found by generating a GUI from a real CLI and opening it in a browser, not by the test suite. Fixed by injecting the token-defining `tailwind.config` script. Also removed a `dark:border-separator-dark` reference to a token never defined anywhere.
- `schema.py`/`cli.py`: the "Build command" output named the wrapped function (e.g. `main`, a Click group's decorated function name) instead of the installed console-script name, producing a command that does not exist. Added a `--prog` flag threaded through `schema.walk()` so callers can supply the real program name.
- `adapters/help_text.py`, the `--from-help` fallback: verified against real non-Python CLIs (clap's `cargo`, cobra's `gh` and `docker`), not just synthetic help text, and found four real gaps in that verification pass:
  - A clap-style repeatable flag (`-v, --verbose...`) leaked its trailing ellipsis into both the flag and the generated dest, producing an unrunnable `--verbose...` on the built command line.
  - A clap-style `<CODE>` metavar kept its closing `>` (`"CODE>"` instead of `"CODE"`), because only the leading bracket was stripped.
  - clap prints its one-line synopsis *before* `Usage:`, not after (unlike argparse/Click); the parser only ever looked after the usage block, so `cargo --help` produced a description made of the second, unrelated `Usage:` continuation line instead of the real "Rust's package manager" synopsis.
  - cobra's own CLIs favor bare, colon-less, often qualified section headers (`USAGE` with the command on the next line, `FLAGS`, `Global Options`, `Common Commands`, `GITHUB ACTIONS COMMANDS`) and colon-suffixed sub-command names (`auth:`). None of that matched the option/command/usage header patterns, which assumed a trailing colon and the bare keyword alone: `gh --help` parsed to an empty tree (no description, no options, no sub-commands) and `docker --help` lost its global flags entirely and folded three unrelated command-group listings into its description. Headers now tolerate an optional colon, an optional qualifier prefix, and (for `Usage`) a synopsis living on the following line; every matching command-group header is now merged instead of just the first.

### Changed

- Removed every em-dash-as-aside from `sprezzature_cli_gui/*.py` docstrings and comments per WRITING.md, and ran `ruff format` across the package.
- Corrected two documentation claims that no longer matched the emitted HTML: README.md said the generated page makes "no network call at runtime", when it in fact loads Tailwind's Play build from a CDN; `scripts/cli_to_gui.py`'s docstring described a Roboto-typeface fallback that the renderer's CSS never implements.

### Added

- **A type gate**, `mypy.ini` plus one CI step. The monorepo carried one while
  the skills lived there; at the split ruff came with the package and mypy did
  not, so no standalone package checked its own annotations. Run by hand, it
  found the `main` defect above in six packages at once. The step runs once, on
  3.12: this is a gate, not a test matrix.
- **`test_mcp_fallback_signature.py`**, which reads the source as a syntax tree
  and so needs neither mypy nor an install, and a case in
  `test_console_scripts_exist.py` ruling out the state where its scan finds no
  candidates and the file reports green while testing nothing. This package has
  one script and advertises no suite command, so that empty result is the right
  answer here and was indistinguishable from a scan that had stopped working.
- **A versioned `.githooks/pre-push`** running the same lint, type and test
  steps as the workflow, in the same order, so a red state cannot reach the
  remote.
- `tests/test_units.py`: unit tests for the pure functions behind the package (`schema.walk` dispatch, both adapters, the help-text fallback parser, the HTML field renderer, `loader.load_parser_from_spec`), on top of the existing end-to-end suite in `tests/test_cli_gui.py`, plus regression tests for every `--from-help` fix listed above.
- LISEZMOI.md, CODING.md, CONTRIBUTING.md, EXAMPLES.md, LANDSCAPE.md/PAYSAGE.md, TRIGGERS.md, Dockerfile, requirements\*.txt, and the `references/` pointer files, matching the structure already in place for sibling `sprezzature-*` packages.
- `tests/test_cli_gui.py::test_installed_console_script_actually_resolves`: runs the installed `sprezzature-cli-gui` console script directly. Every other CLI-level test in the suite drove the legacy, unpackaged `scripts/cli_to_gui.py` facade instead, so a typo in `pyproject.toml`'s `[project.scripts]` entry would have passed CI (setuptools does not import the target at install time) and only broken the moment a real user typed the command.

## v1.0.0 (2026-07-29)

Initial standalone release, extracted from the `sprezzature` monorepo.

### Package

- `sprezzature_cli_gui/loader.py`: resolves a `module:factory` or `path.py:factory` spec down to a parser object.
- `sprezzature_cli_gui/schema.py`: the shared parser-tree shape and the `walk()` dispatcher.
- `sprezzature_cli_gui/adapters/`: one adapter per supported framework (argparse, Click and, through Click, Typer) plus the `--from-help` fallback that works on any CLI, Python or not.
- `sprezzature_cli_gui/renderer.py`: turns the parser tree into a single self-contained HTML page.
- `sprezzature_cli_gui/cli.py`: the `sprezzature-cli-gui` command-line entry point.
- `scripts/cli_to_gui.py`: a thin facade re-exporting the package's public API, kept for anyone already scripting against the pre-split single-file layout.
