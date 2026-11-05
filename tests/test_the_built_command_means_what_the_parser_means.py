"""
The command line the page builds must mean what the parser means.

Every other test of the renderer checks that a field exists. These check what
the field *does*: the line the "Build command" button assembles, run through
the parser it came from, has to land on the values the visitor chose, and an
untouched form has to land on the parser's own defaults. Four ways it did not:

* an argparse ``store_false`` flag (``--no-cache``) rendered pre-checked,
  because its default is ``True``, so the untouched form built
  ``--no-cache`` and turned caching off;
* a ``count`` option (``-v``, ``action="count"`` or Click's ``count=True``)
  rendered as a number field and built ``-v 3``, which both parsers reject;
* a Click ``--color/--no-color`` pair kept only ``--color``, so the page
  could never build the off spelling;
* the program name was pasted raw into the script, so a quote ended the
  string literal and a ``</script>`` ended the script.

The assembly runs in the visitor's browser, so the strongest check runs the
page's own JavaScript under ``node``, fed from the attributes the page
actually carries, and parses the result with the real parser. The
attribute-level tests above it need no JavaScript runtime.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import click
import pytest

from sprezzature_cli_gui.audit import audit
from sprezzature_cli_gui.renderer import render_html
from sprezzature_cli_gui.schema import walk

# ── reading the page the way the browser script does ───────────────────────


class _Fields(HTMLParser):
    """Collect, per form, the attributes the page's script reads."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "form" and "data-cli-form" in a:
            self.forms.append({"sub": a.get("data-subcommand") or "", "fields": []})
        elif "data-cli-flag" in a and self.forms:
            field: dict[str, Any] = {
                "flag": a["data-cli-flag"],
                "type": a.get("type") or tag,
                "checked": "checked" in a,
                "value": a.get("value") or "",
            }
            for key in ("data-cli-flag-off", "data-cli-default", "data-cli-count"):
                if key in a:
                    field[key] = a[key]
            if tag == "select":
                field["value"] = ""
            self.forms[-1]["fields"].append(field)


def _forms(page: str) -> list[dict[str, Any]]:
    parser = _Fields()
    parser.feed(page)
    return parser.forms


def _field(page: str, flag: str) -> dict[str, Any]:
    for form in _forms(page):
        for field in form["fields"]:
            if field["flag"] == flag:
                return field
    raise AssertionError(f"no field for {flag}")


def _argparse_tool() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tool")
    parser.add_argument("--no-cache", dest="cache", action="store_false")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--color", action=argparse.BooleanOptionalAction, default=True)
    return parser


@click.command()
@click.option("--color/--no-color", default=True)
@click.option("--shout/--no-shout", default=False)
@click.option("-v", "--verbose", count=True)
def _click_tool(color: bool, shout: bool, verbose: int) -> None:
    """A tool with an on/off pair and a counter."""


# ── attributes: no JavaScript runtime needed ───────────────────────────────


def test_a_store_false_flag_is_not_pre_checked() -> None:
    """Checked means "pass this flag"; an untouched form passes nothing."""
    page = render_html(walk(_argparse_tool()))
    assert _field(page, "--no-cache")["checked"] is False


def test_a_count_option_is_marked_as_a_count() -> None:
    """Both parsers' counters carry the marker the script repeats on."""
    for page in (render_html(walk(_argparse_tool())), render_html(walk(_click_tool))):
        field = _field(page, "-v")
        assert field["type"] == "number"
        assert "data-cli-count" in field


def test_an_on_off_pair_keeps_its_off_spelling() -> None:
    """Click's secondary flag and argparse's BooleanOptionalAction both survive."""
    click_page = render_html(walk(_click_tool))
    color = _field(click_page, "--color")
    assert color["type"] == "checkbox"
    assert color["data-cli-flag-off"] == "--no-color"
    assert color["checked"] is True and color["data-cli-default"] == "true"
    assert _field(click_page, "--shout")["checked"] is False

    argparse_color = _field(render_html(walk(_argparse_tool())), "--color")
    assert argparse_color["type"] == "checkbox"
    assert argparse_color["data-cli-flag-off"] == "--no-color"


_NASTY = 'it\'s "x" </script><script>alert(1)</script>'


def test_a_program_name_cannot_break_out_of_the_script() -> None:
    """The name is encoded, and the module script ends where it should."""
    tree = walk(argparse.ArgumentParser(prog=_NASTY))
    page = render_html(tree)
    module = page.split('<script type="module">', 1)[1]
    script, _ = module.split("</script>", 1)
    assert "addEventListener" in script, "the script was cut short by the program name"
    assert "<script>alert(1)" not in page


def test_the_audit_reads_an_encoded_program_name() -> None:
    """A clean page with an awkward name is still clean."""
    tree = walk(argparse.ArgumentParser(prog=_NASTY))
    assert audit(tree, render_html(tree)) == []


def test_the_audit_still_reads_a_page_from_before_the_encoding() -> None:
    """Pages committed by 1.4.0 and earlier seed with a single-quoted literal."""
    tree = walk(argparse.ArgumentParser(prog="demo"))
    page = render_html(tree)
    legacy = re.sub(r"const parts = \[[^\]]*\]", "const parts = ['demo']", page)
    assert "const parts = ['demo']" in legacy
    assert audit(tree, legacy) == []


# ── behaviour: the page's own script, under node ───────────────────────────


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        # A skip reads as a pass. Locally that is tolerable; on CI, where
        # the runner image ships node, a missing one means this file checked
        # nothing, and that has to be loud.
        if os.environ.get("CI"):
            pytest.fail("node is missing on CI; the page's script went unchecked")
        pytest.skip("node is not installed")
    return node


def _build(page: str, form_index: int, edits: dict[str, Any], tmp_path: Path) -> list[str]:
    """Run the page's ``addParts`` on one form's fields, after ``edits``."""
    script = page.split('<script type="module">', 1)[1].split("</script>", 1)[0]
    start = script.index("const escape")
    end = script.index("document.querySelectorAll")
    library = script[start:end]
    seed = json.loads(re.search(r"const parts = (\[.*?\]);", script).group(1))  # type: ignore[union-attr]
    form = _forms(page)[form_index]
    fields = []
    for field in form["fields"]:
        field = {**field, **edits.get(field["flag"], {})}
        fields.append(
            {
                "flag": field["flag"],
                "checkbox": field["type"] == "checkbox",
                "checked": field["checked"],
                "value": str(field["value"]),
                "off": field.get("data-cli-flag-off"),
                "def": field.get("data-cli-default") == "true",
                "count": "data-cli-count" in field,
            }
        )
    program = (
        f"{library}\n"
        f"const parts = {json.dumps(seed)};\n"
        f"addParts(parts, {json.dumps(form['sub'])}, {json.dumps(fields)});\n"
        "console.log(JSON.stringify(parts));\n"
    )
    source = tmp_path / "build.mjs"
    source.write_text(program, encoding="utf-8")
    out = subprocess.run([_node(), str(source)], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_the_untouched_form_builds_the_parsers_defaults(tmp_path: Path) -> None:
    """argparse: the default page, parsed back, equals parse_args([])."""
    parser = _argparse_tool()
    page = render_html(walk(parser))
    argv = _build(page, 0, {}, tmp_path)[1:]
    assert vars(parser.parse_args(argv)) == vars(parser.parse_args([]))


def test_ticking_and_counting_build_what_the_visitor_chose(tmp_path: Path) -> None:
    """argparse: ticked --no-cache, three -v and --color unticked."""
    parser = _argparse_tool()
    page = render_html(walk(parser))
    edits = {
        "--no-cache": {"checked": True},
        "-v": {"value": "3"},
        "--color": {"checked": False},
    }
    args = parser.parse_args(_build(page, 0, edits, tmp_path)[1:])
    assert (args.cache, args.verbose, args.color) == (False, 3, False)


def test_a_click_pair_and_counter_round_trip(tmp_path: Path) -> None:
    """Click: the off spelling is reachable and the counter repeats."""
    page = render_html(walk(_click_tool, prog="tool"))
    default_argv = _build(page, 0, {}, tmp_path)[1:]
    ctx = _click_tool.make_context("tool", default_argv)
    assert ctx.params == {"color": True, "shout": False, "verbose": 0}

    edits = {"--color": {"checked": False}, "--shout": {"checked": True}, "-v": {"value": "2"}}
    ctx = _click_tool.make_context("tool", _build(page, 0, edits, tmp_path)[1:])
    assert ctx.params == {"color": False, "shout": True, "verbose": 2}


def test_the_seed_is_the_program_name_even_when_it_is_awkward(tmp_path: Path) -> None:
    """The built line starts with the exact name, quotes and all."""
    parser = argparse.ArgumentParser(prog=_NASTY)
    parser.add_argument("--quiet", action="store_true")
    page = render_html(walk(parser))
    assert _build(page, 0, {}, tmp_path) == [_NASTY]
