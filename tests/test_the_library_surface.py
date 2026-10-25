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


# ── One front door ─────────────────────────────────────────────────────────


def test_the_command_is_installed_and_the_twin_name_is_gone() -> None:
    """
    One console script, not two.

    There were two until 2026-10-25 — ``sprezzature-cli-gui`` (argparse) and
    ``sprezzature-cli-gui-click`` — and the second existed only to distinguish
    a twin that wrapped the first. The suffixed name goes with it: a command
    whose whole meaning was "the other parser" names nothing now.

    Read with a regex, not ``tomllib``: that module is standard library only
    from 3.11, and this package supports 3.10.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[project\.scripts\]\s*$(.*?)(?=^\[|\Z)", pyproject, re.M | re.S)
    assert section, "pyproject.toml declares no console scripts at all"
    scripts = dict(re.findall(r'^([A-Za-z0-9._-]+)\s*=\s*"([^"]+)"', section.group(1), re.M))
    assert scripts["sprezzature-cli-gui"] == "sprezzature_cli_gui.cli:main"
    assert "sprezzature-cli-gui-click" not in scripts


def test_click_is_a_base_dependency_and_no_second_parser_grows_back() -> None:
    """
    With argparse gone, nothing ships with Python that can parse a command
    line, so click cannot be optional.

    And the work now lives in `_generate`, reachable without a parser at all —
    which is what stops a second front door from being written as a wrapper
    around the first, the way the removed one was.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    base = re.search(r"^dependencies\s*=\s*\[(.*?)\]", pyproject, re.M | re.S)
    assert base and "click" in base.group(1)
    assert not re.search(r"^click\s*=\s*\[", pyproject, re.M)

    pkg = root / "sprezzature_cli_gui"
    assert not (pkg / "cli_click.py").exists()
    assert "import argparse" not in (pkg / "cli.py").read_text(encoding="utf-8")
    assert (pkg / "_generate.py").is_file()


def test_the_page_is_the_same_whichever_way_it_is_asked_for(tmp_path) -> None:
    """
    The command and the library path must agree.

    This replaces a test that compared two front doors. There is one now, so
    the comparison that still means something is between the command and
    calling `_generate` directly — which is what the HTTP and MCP surfaces do.
    """
    import subprocess
    import sys

    from sprezzature_cli_gui._generate import build_tree, render

    cli = tmp_path / "tiny_cli.py"
    cli.write_text(
        "import argparse\n"
        "def build():\n"
        "    p = argparse.ArgumentParser(prog='tiny')\n"
        "    p.add_argument('--name', help='who')\n"
        "    return p\n"
    )
    spec = f"{cli}:build"

    direct = render(build_tree(spec), title=None)
    done = subprocess.run(
        [sys.executable, "-m", "sprezzature_cli_gui.cli", spec],
        capture_output=True,
        text=True,
        check=True,
    )
    assert done.stdout == direct
