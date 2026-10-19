"""
The library the HTTP surface tells callers to use must exist.

This package's best decision is a refusal: ``POST /v1/render`` takes a schema
tree and will **not** take a ``module:factory`` spec, because importing an
arbitrary module named by an unauthenticated caller is remote code execution
and no allow-list makes it safe enough to be worth it. The refusal sends the
caller to the library instead — "introspect your own parser, in your own
process, with ``walk(parser)``, and post the tree".

That was sound advice pointing at nothing: ``import sprezzature_cli_gui``
exported a version string. The refusal and the alternative are one design, and
half of it was missing.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse

import pytest

import sprezzature_cli_gui


def test_the_package_exports_an_engine_not_a_version_string() -> None:
    """A library surface that exports no callable is not a library surface."""
    callables = [
        name
        for name in sprezzature_cli_gui.__all__
        if not name.startswith("__") and callable(getattr(sprezzature_cli_gui, name))
    ]
    assert len(callables) >= 3


def test_the_two_halves_of_the_job_are_both_reachable() -> None:
    """`walk` reads a parser, `render_html` writes the page. Both, by name."""
    assert callable(sprezzature_cli_gui.walk)
    assert callable(sprezzature_cli_gui.render_html)


def test_the_path_the_refusal_points_at_actually_works() -> None:
    """The whole round trip the API's error message describes."""
    parser = argparse.ArgumentParser(prog="greet", description="Say hello.")
    parser.add_argument("--name", help="who to greet")
    parser.add_argument("--loud", action="store_true", help="shout it")

    tree = sprezzature_cli_gui.walk(parser)
    assert tree["prog"] == "greet"
    assert {action["dest"] for action in tree["actions"]} >= {"name", "loud"}

    page = sprezzature_cli_gui.render_html(tree, title="Greet")
    assert page.lstrip().lower().startswith("<!doctype html")
    assert "greet" in page.lower()


def test_the_audit_agrees_with_a_page_it_just_rendered() -> None:
    """A page built from a tree must not disagree with that tree."""
    parser = argparse.ArgumentParser(prog="greet")
    parser.add_argument("--name")
    tree = sprezzature_cli_gui.walk(parser)
    assert sprezzature_cli_gui.audit(tree, sprezzature_cli_gui.render_html(tree)) == []


def test_importing_the_library_needs_no_extra() -> None:
    """`walk` on an argparse parser is standard library only.

    That matters here more than elsewhere: the caller is being asked to run
    this *inside their own process*, beside their own CLI, and a library that
    dragged click and typer in would make that a bigger ask than the thing it
    is replacing.
    """
    import subprocess
    import sys
    import textwrap

    done = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import sys
                BLOCKED = ("click", "typer", "fastapi", "pydantic")
                class Blocker:
                    def find_spec(self, name, path=None, target=None):
                        if name.split(".")[0] in BLOCKED:
                            raise ImportError("blocked: " + name)
                        return None
                sys.meta_path.insert(0, Blocker())

                import argparse
                from sprezzature_cli_gui import walk, render_html
                parser = argparse.ArgumentParser(prog="greet")
                parser.add_argument("--name")
                assert walk(parser)["prog"] == "greet"
                assert render_html(walk(parser))
                print("OK")
                """
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr[-1500:]
    assert "OK" in done.stdout


def test_an_unknown_name_is_an_attribute_error() -> None:
    """A typo should read as a typo."""
    with pytest.raises(AttributeError):
        sprezzature_cli_gui.definitely_not_a_tool


# ── The two front doors ────────────────────────────────────────────────────


def test_both_front_doors_are_installed() -> None:
    """argparse because it is always there, Click because this package reads it.

    A tool whose job is turning Click commands into forms, not offering a
    Click front door of its own, is a gap a reader notices before the README
    does.
    """
    from pathlib import Path

    import tomllib

    root = Path(__file__).resolve().parent.parent
    scripts = tomllib.loads((root / "pyproject.toml").read_text())["project"]["scripts"]
    assert "sprezzature-cli-gui" in scripts
    assert "sprezzature-cli-gui-click" in scripts


def test_the_two_front_doors_emit_the_same_page(tmp_path) -> None:
    """Same flags, same handler — so the output cannot differ.

    Checked on the output rather than on the flag lists: two parsers can
    declare the same options and still disagree about what one of them means,
    and that disagreement only shows in what comes out.
    """
    import json
    import subprocess
    import sys

    cli = tmp_path / "tiny_cli.py"
    cli.write_text(
        "import argparse\n"
        "def build():\n"
        "    p = argparse.ArgumentParser(prog='tiny')\n"
        "    p.add_argument('--name', help='who')\n"
        "    return p\n"
    )
    spec = f"{cli}:build"

    from sprezzature_cli_gui import cli as argparse_cli

    def capture(module, argv):
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            module.main(argv)
        return buffer.getvalue()

    first = capture(argparse_cli, [spec, "--json"])
    second = subprocess.run(
        [sys.executable, "-m", "sprezzature_cli_gui.cli_click", spec, "--json"],
        capture_output=True,
        text=True,
    )
    if second.returncode == 1 and "Click" in second.stderr:
        pytest.skip("the click extra is not installed here")
    assert json.loads(first) == json.loads(second.stdout)


def test_the_click_twin_names_its_extra_when_click_is_absent() -> None:
    """A command on PATH that cannot start has its message as its interface."""
    import subprocess
    import sys
    import textwrap

    done = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                import sys
                class Blocker:
                    def find_spec(self, name, path=None, target=None):
                        if name.split(".")[0] == "click":
                            raise ImportError("blocked")
                        return None
                sys.meta_path.insert(0, Blocker())
                from sprezzature_cli_gui.cli_click import main
                try:
                    main()
                except SystemExit as exit_code:
                    print("exit", exit_code.code)
                """
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert "sprezzature-cli-gui[click]" in done.stderr, done.stderr[-400:]
    assert "argparse front door" in done.stderr
