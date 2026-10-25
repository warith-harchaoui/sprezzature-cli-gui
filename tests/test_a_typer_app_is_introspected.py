"""
A Typer app, walked without being run.

The README, the SKILL and three module docstrings all said Typer was
supported. It was not. ``schema.walk`` type-dispatched on
``argparse.ArgumentParser`` and ``click.Command`` only, and a ``typer.Typer``
is neither — so it fell through to the refusal. The route the click adapter
named, ``app.cli``, does not exist on typer 0.20; that was checked rather than
assumed.

Worse than the refusal was what happened one layer down. ``loader`` calls the
thing a spec names unless it already looks like a parser, and that list knew
about ``click.Command`` — which is callable — but not about ``typer.Typer``,
which is callable too. So `sprezzature-cli-gui mod:app` on a Typer app **ran
the app**, and the user saw "No such command 'mod:app'" in Typer's own rich
box: an error that reads as their CLI rejecting their spec, when this loader
had just invoked it.

These tests pin both halves, and the second one is the one that mattered.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from sprezzature_cli_gui.loader import load_parser_from_spec
from sprezzature_cli_gui.schema import walk

typer = pytest.importorskip("typer", reason="the typer extra is not installed")


@pytest.fixture()
def app_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """A two-command Typer app, importable, exposed both ways."""
    module = tmp_path / "typer_fixture.py"
    module.write_text(
        "import typer\n\n"
        'app = typer.Typer(help="A demo Typer app.")\n\n\n'
        "@app.command()\n"
        "def greet(name: str, loud: bool = False, times: int = 1):\n"
        '    """Greet someone."""\n\n\n'
        "@app.command()\n"
        "def farewell(name: str, formal: bool = True):\n"
        '    """Say goodbye."""\n\n\n'
        "def build():\n"
        "    return app\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return "typer_fixture"


# ----------------------------------------------------------------- walking


def test_a_typer_app_walks_into_the_canonical_tree(app_module: str) -> None:
    """Both sub-commands and their parameters survive the conversion."""
    import importlib

    app = importlib.import_module(app_module).app
    tree = walk(app, prog="typer-demo")

    assert tree["prog"] == "typer-demo"
    assert set(tree["sub_commands"]) == {"greet", "farewell"}
    greet = tree["sub_commands"]["greet"]
    assert {action["dest"] for action in greet["actions"]} >= {"name", "loud", "times"}


def test_prog_is_honoured_because_typer_cannot_know_it(app_module: str) -> None:
    """
    A Typer command's name comes from the decorated function, which is rarely
    the installed console-script name — the same reason `--prog` exists for
    Click groups. Without it the page builds a command line nobody can run.
    """
    import importlib

    app = importlib.import_module(app_module).app
    assert walk(app)["prog"] != "typer-demo"
    assert walk(app, prog="typer-demo")["prog"] == "typer-demo"


def test_the_refusal_names_all_three_frameworks() -> None:
    """A reader who passed the wrong object needs to know what is accepted."""
    with pytest.raises(TypeError) as caught:
        walk(object())
    message = str(caught.value)
    assert "argparse.ArgumentParser" in message
    assert "click.Command" in message
    assert "typer.Typer" in message


# ------------------------------------------------------------ not running it


def test_naming_a_typer_app_does_not_run_it(app_module: str) -> None:
    """
    The bug this file exists for.

    ``typer.Typer`` is callable, so the loader used to invoke it: the app ran
    against the current argv and answered "No such command", which looks like
    the user's own CLI refusing their spec. If this ever regresses, the call
    below raises SystemExit instead of returning an object.
    """
    obj = load_parser_from_spec(f"{app_module}:app")
    assert isinstance(obj, typer.Typer)


def test_a_factory_returning_a_typer_app_is_accepted(app_module: str) -> None:
    """The documented contract — a zero-argument factory — works too."""
    obj = load_parser_from_spec(f"{app_module}:build")
    assert isinstance(obj, typer.Typer)


def test_both_spec_forms_produce_the_same_tree(app_module: str) -> None:
    """Naming the object and naming a factory for it cannot disagree."""
    direct = walk(load_parser_from_spec(f"{app_module}:app"), prog="x")
    made = walk(load_parser_from_spec(f"{app_module}:build"), prog="x")
    assert direct == made


def test_argparse_and_click_still_load(app_module: str, tmp_path: Path) -> None:
    """
    The other two frameworks are untouched.

    argparse in particular: it is the parser that ships with Python and most of
    the CLIs this tool exists to wrap are built with it, including 63 of the
    suite's own per-tool scripts.
    """
    module = tmp_path / "mixed_fixture.py"
    module.write_text(
        "import argparse\n"
        "import click\n\n"
        "def ap():\n"
        "    p = argparse.ArgumentParser(prog='ap')\n"
        "    p.add_argument('--name')\n"
        "    return p\n\n"
        "@click.command()\n"
        "@click.option('--name')\n"
        "def cl(name):\n"
        '    """A click command."""\n',
        encoding="utf-8",
    )
    assert isinstance(load_parser_from_spec("mixed_fixture:ap"), argparse.ArgumentParser)
    walked = walk(load_parser_from_spec("mixed_fixture:cl"), prog="cl")
    assert walked["prog"] == "cl"
