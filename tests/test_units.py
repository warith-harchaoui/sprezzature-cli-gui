"""Unit tests for the individual pieces behind sprezzature-cli-gui.

tests/test_cli_gui.py already covers the package end to end (import,
--help, a full argparse-to-HTML run through the subprocess entry point).
This file exercises the modules underneath directly: the schema
dispatcher, each framework adapter, the help-text fallback parser, the
HTML field renderer, and the module:factory loader. Click is an optional
extra (``pip install "sprezzature-cli-gui[click]"``), so the Click-only
tests are skipped when it is not installed.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from sprezzature_cli_gui import renderer, schema
from sprezzature_cli_gui.adapters import argparse as argparse_adapter
from sprezzature_cli_gui.adapters import help_text
from sprezzature_cli_gui.loader import load_parser_from_spec

# ── schema ───────────────────────────────────────────────────────────────────


def test_safe_default_passthrough_and_suppress() -> None:
    """_safe_default keeps JSON-native types and maps SUPPRESS/None to None."""
    assert schema._safe_default(argparse.SUPPRESS) is None
    assert schema._safe_default(None) is None
    assert schema._safe_default("x") == "x"
    assert schema._safe_default(3) == 3
    assert schema._safe_default(3.5) == 3.5
    assert schema._safe_default(True) is True


def test_safe_default_recurses_into_sequences_and_stringifies_the_rest() -> None:
    """_safe_default recurses into list/tuple and falls back to str() otherwise."""
    assert schema._safe_default([1, "a", None]) == [1, "a", None]
    assert schema._safe_default((1, 2)) == [1, 2]

    class Weird:
        def __str__(self) -> str:
            return "weird-value"

    assert schema._safe_default(Weird()) == "weird-value"


def test_walk_dispatches_argparse() -> None:
    """walk() routes an ArgumentParser to the argparse adapter."""
    p = argparse.ArgumentParser(prog="demo")
    p.add_argument("--name", default="world")
    tree = schema.walk(p)
    assert tree["prog"] == "demo"
    assert any(a["dest"] == "name" for a in tree["actions"])


def test_walk_rejects_unknown_object() -> None:
    """walk() raises TypeError for anything that is neither argparse nor Click."""
    with pytest.raises(TypeError):
        schema.walk(object())


def test_walk_prog_override_replaces_argparse_own_prog() -> None:
    """walk(..., prog=...) overrides even an explicitly-set ArgumentParser.prog."""
    p = argparse.ArgumentParser(prog="demo")
    p.add_argument("--name", default="world")
    tree = schema.walk(p, prog="installed-name")
    assert tree["prog"] == "installed-name"


def test_walk_prog_override_replaces_click_group_function_name() -> None:
    """walk(..., prog=...) fixes the Click case where Group.name is the
    decorated function's name, not the installed console-script name."""
    click = pytest.importorskip("click")

    @click.group()
    def main() -> None:
        """Root group named after its Python function, not its console script."""

    tree = schema.walk(main)
    assert tree["prog"] == "main"  # unfixed: Click's own default is wrong here

    tree = schema.walk(main, prog="my-tool")
    assert tree["prog"] == "my-tool"


# ── adapters.argparse ────────────────────────────────────────────────────────


def test_action_kind_covers_every_field_shape() -> None:
    """_action_kind maps each argparse action shape to the right form-field kind."""
    p = argparse.ArgumentParser()
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--mode", choices=["fast", "slow"])
    p.add_argument("--count", type=int)
    p.add_argument("--ratio", type=float)
    p.add_argument("--name")
    by_dest = {a.dest: a for a in p._actions}
    assert argparse_adapter._action_kind(by_dest["verbose"]) == "bool"
    assert argparse_adapter._action_kind(by_dest["mode"]) == "choice"
    assert argparse_adapter._action_kind(by_dest["count"]) == "int"
    assert argparse_adapter._action_kind(by_dest["ratio"]) == "float"
    assert argparse_adapter._action_kind(by_dest["name"]) == "text"


def test_walk_parser_recurses_into_subparsers_and_drops_help_version() -> None:
    """walk_parser nests sub-commands and filters --help/--version from actions."""
    p = argparse.ArgumentParser(prog="tool")
    p.add_argument("-V", "--version", action="version", version="tool 1.0")
    sub = p.add_subparsers()
    child = sub.add_parser("build", help="Build the thing")
    child.add_argument("--out", required=True)

    tree = argparse_adapter.walk_parser(p)
    assert tree["actions"] == []  # --help / --version both filtered
    assert "build" in tree["sub_commands"]
    child_tree = tree["sub_commands"]["build"]
    assert child_tree["actions"][0]["dest"] == "out"
    assert child_tree["actions"][0]["required"] is True


# ── adapters.click (optional extra) ─────────────────────────────────────────


def test_click_param_kind_and_choices() -> None:
    """The Click adapter reads is_flag/count/type.name into the same kind vocabulary."""
    click = pytest.importorskip("click")
    from sprezzature_cli_gui.adapters import click as click_adapter

    @click.command()
    @click.option("--verbose", is_flag=True)
    @click.option("-v", "--verbosity", count=True)
    @click.option("--format", type=click.Choice(["mp3", "ogg"]))
    @click.option("--threshold", type=float)
    @click.argument("path", type=click.Path())
    def cmd(verbose, verbosity, format, threshold, path):  # noqa: A002
        """A demo command."""

    by_name = {p.name: p for p in cmd.params}
    assert click_adapter._click_param_kind(by_name["verbose"]) == "bool"
    assert click_adapter._click_param_kind(by_name["verbosity"]) == "int"
    assert click_adapter._click_param_kind(by_name["format"]) == "choice"
    assert click_adapter._click_param_kind(by_name["threshold"]) == "float"
    assert click_adapter._click_param_kind(by_name["path"]) == "file"
    assert click_adapter._click_param_choices(by_name["format"]) == ["mp3", "ogg"]


def test_walk_click_nests_groups() -> None:
    """walk_click recurses into a Group's sub-commands the same way argparse does."""
    click = pytest.importorskip("click")
    from sprezzature_cli_gui.adapters.click import walk_click

    @click.group()
    def cli():
        """Root group."""

    @cli.command()
    @click.option("--name", default="world", help="Who to greet")
    def greet(name):
        """Say hello."""

    tree = walk_click(cli, prog="mytool")
    assert tree["prog"] == "mytool"
    assert "greet" in tree["sub_commands"]
    assert tree["sub_commands"]["greet"]["actions"][0]["dest"] == "name"
    assert tree["sub_commands"]["greet"]["actions"][0]["default"] == "world"


# ── adapters.help_text ───────────────────────────────────────────────────────


def test_extract_prog_prefers_the_usage_line() -> None:
    """_extract_prog reads the tool's own prog name off the Usage: line."""
    help_out = "usage: mytool [-h] [--verbose] {build,test} ...\n"
    assert help_text._extract_prog("python3 mytool.py", help_out) == "mytool"


def test_extract_prog_falls_back_to_the_command_basename() -> None:
    """With no usage line, _extract_prog skips the interpreter and strips .py."""
    assert help_text._extract_prog("python3 path/to/mycli.py", "") == "mycli"


def test_parse_option_line_reads_flags_default_and_choices() -> None:
    """_parse_option_line recovers flags, a metavar-based kind, and [default: …]."""
    line = "  --format TEXT  Output format [mp3|ogg|flac] [default: mp3]"
    action = help_text._parse_option_line(line)
    assert action is not None
    assert action["flags"] == ["--format"]
    assert action["choices"] == ["mp3", "ogg", "flac"]
    assert action["default"] == "mp3"
    assert action["kind"] == "choice"


def test_parse_option_line_bare_flag_is_boolean_and_help_filtered() -> None:
    """A flag with no metavar reads as boolean; -h/--help is filtered out."""
    action = help_text._parse_option_line("  --verbose  Enable verbose output")
    assert action is not None
    assert action["kind"] == "bool"
    assert help_text._parse_option_line("  -h, --help  Show this message and exit.") is None


def test_parse_options_section_folds_every_continuation_line() -> None:
    """A help line wrapped onto several indented lines is folded into one action."""
    section = (
        "  --input PATH\n"
        "                        Path to the input file, read once at\n"
        "                        startup.\n"
    )
    actions = help_text._parse_options_section(section)
    assert len(actions) == 1
    assert actions[0]["help"] == "Path to the input file, read once at startup."


def test_parse_commands_section() -> None:
    """_parse_commands_section reads a Commands: block into (name, help) pairs."""
    section = "  build   Build the project\n  test    Run the tests\n"
    assert help_text._parse_commands_section(section) == [
        ("build", "Build the project"),
        ("test", "Run the tests"),
    ]


def test_walk_from_help_uses_the_injected_help_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """walk_from_help builds the canonical tree from a stubbed --help transcript."""
    canned = textwrap.dedent("""\
        usage: mytool [-h] [--verbose] INPUT

        A demo tool.

        options:
          -h, --help     show this help message and exit
          --verbose      Enable verbose output
    """)
    monkeypatch.setattr(help_text, "_run_help", lambda cmdline: canned)
    tree = help_text.walk_from_help("mytool")
    assert tree["prog"] == "mytool"
    assert tree["description"] == "A demo tool."
    assert any(a["flags"] == ["--verbose"] for a in tree["actions"])
    assert tree["sub_commands"] == {}


# ── renderer ─────────────────────────────────────────────────────────────────


def test_e_escapes_html_special_characters() -> None:
    """_e() escapes quotes and angle brackets for safe attribute embedding."""
    assert renderer._e('<b>"x"</b>') == "&lt;b&gt;&quot;x&quot;&lt;/b&gt;"


def test_field_html_renders_checkbox_for_bool_kind() -> None:
    """A bool action renders a checkbox input, not a text field."""
    action = {
        "dest": "verbose",
        "flags": ["--verbose"],
        "kind": "bool",
        "default": False,
        "required": False,
        "help": "",
        "choices": None,
    }
    html = renderer._field_html(action, prefix="")
    assert 'type="checkbox"' in html
    assert 'data-cli-flag="--verbose"' in html


def test_field_html_renders_select_for_choice_kind() -> None:
    """A choice action renders a <select> with one <option> per choice."""
    action = {
        "dest": "format",
        "flags": ["--format"],
        "kind": "choice",
        "default": "mp3",
        "required": False,
        "help": "",
        "choices": ["mp3", "ogg"],
    }
    html = renderer._field_html(action, prefix="")
    assert "<select" in html
    assert 'value="mp3" selected' in html
    assert 'value="ogg">' in html


def test_render_html_includes_prog_title_and_fields() -> None:
    """render_html produces a full document naming the prog and every field."""
    tree = {
        "prog": "demo",
        "description": "A demo CLI",
        "actions": [
            {
                "dest": "name",
                "flags": ["--name"],
                "kind": "text",
                "default": "world",
                "required": False,
                "help": "Who to greet",
                "choices": None,
            },
        ],
        "sub_commands": {},
    }
    html = renderer.render_html(tree, title="Demo")
    assert "<title>Demo</title>" in html
    assert "demo" in html
    assert 'data-cli-flag="--name"' in html
    assert "'demo'" in html  # <<PROG>> substitution in the JS payload


def test_render_html_defines_every_custom_color_token_it_uses() -> None:
    """Every semantic Tailwind color class the page emits (brand-blue,
    label-primary/secondary, surface-secondary, separator) must be defined
    in an inline tailwind.config block, or the Play CDN silently drops the
    utility and the field renders unstyled. Concretely this was the
    'Build command' button rendering as invisible white-on-white: it uses
    bg-brand-blue and text-white, and an undefined bg-brand-blue produced no
    background at all."""
    tree = {"prog": "demo", "description": "", "actions": [], "sub_commands": {}}
    html = renderer.render_html(tree)
    assert "tailwind.config" in html
    for token in ("brand", "label", "surface", "separator"):
        assert f"{token}:" in html or f"'{token}'" in html
    # tailwind.config must appear after the CDN <script> tag loads the
    # `tailwind` global; setting it before that point would throw.
    assert html.index("cdn.tailwindcss.com") < html.index("tailwind.config")


def test_field_html_never_references_the_undefined_separator_dark_token() -> None:
    """border-separator has one alpha-channel value in the sprezzature-ui
    design system with no dedicated dark twin (see stack-tailwind.md); a
    'separator-dark' class name was never defined anywhere, so
    dark:border-separator-dark silently dropped the border color in dark
    mode."""
    action = {
        "dest": "name",
        "flags": ["--name"],
        "kind": "text",
        "default": None,
        "required": False,
        "help": "",
        "choices": None,
    }
    html = renderer._field_html(action, prefix="")
    assert "separator-dark" not in html


# ── loader ───────────────────────────────────────────────────────────────────


def test_load_parser_from_spec_file_path(tmp_path: Path) -> None:
    """A 'path/to/file.py:factory' spec loads the file and calls the factory."""
    cli_file = tmp_path / "mycli.py"
    cli_file.write_text(
        textwrap.dedent("""\
            import argparse

            def make_parser():
                p = argparse.ArgumentParser(prog="mycli")
                p.add_argument("--x")
                return p
        """),
        encoding="utf-8",
    )
    parser = load_parser_from_spec(f"{cli_file}:make_parser")
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "mycli"


def test_load_parser_from_spec_accepts_an_already_built_parser(tmp_path: Path) -> None:
    """A spec naming the parser object itself (not a factory) works too."""
    cli_file = tmp_path / "mycli.py"
    cli_file.write_text(
        textwrap.dedent("""\
            import argparse

            parser = argparse.ArgumentParser(prog="mycli")
            parser.add_argument("--x")
        """),
        encoding="utf-8",
    )
    parser = load_parser_from_spec(f"{cli_file}:parser")
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.prog == "mycli"


def test_load_parser_from_spec_does_not_invoke_a_raw_click_command(tmp_path: Path) -> None:
    """A spec naming a click.Command directly is used as is, never called.

    Calling a click.Command runs it for real (click.BaseCommand.__call__
    invokes main()); this test would hang or raise SystemExit if the
    loader ever called the object instead of returning it.
    """
    pytest.importorskip("click")
    cli_file = tmp_path / "mycli.py"
    cli_file.write_text(
        textwrap.dedent("""\
            import click

            @click.command()
            @click.option("--name", default="world")
            def cli(name):
                pass
        """),
        encoding="utf-8",
    )
    result = load_parser_from_spec(f"{cli_file}:cli")
    import click

    assert isinstance(result, click.Command)


def test_load_parser_from_spec_requires_a_colon() -> None:
    """A spec with no ':' separator is rejected up front."""
    with pytest.raises(ValueError):
        load_parser_from_spec("no_colon_here")


def test_load_parser_from_spec_missing_file(tmp_path: Path) -> None:
    """A file-path spec pointing at a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_parser_from_spec(f"{tmp_path / 'missing.py'}:make_parser")


def test_load_parser_from_spec_rejects_wrong_return_type(tmp_path: Path) -> None:
    """A factory that returns neither an argparse parser nor a Click command errors."""
    cli_file = tmp_path / "bad.py"
    cli_file.write_text("def make_parser():\n    return object()\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_parser_from_spec(f"{cli_file}:make_parser")
