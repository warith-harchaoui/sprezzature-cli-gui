"""
Every command this package installs is a click command.

The suite's own command lines are click only since 2026-11-04. The last
argparse one here was ``sprezzature-cli-gui-mcp``, whose ``--help`` printed a
lowercase ``usage:`` while the two other commands printed click's ``Usage:``.

This package is the one place where argparse stays legitimately: reading a
user's argparse parser is its job. So the import check is an allow-list of the
modules that read parsers, and anything else that imports argparse is a
command line that grew back.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Regex rather than tomllib, which is stdlib only from 3.11 (the floor is 3.10).
_SCRIPTS_SECTION_RE = re.compile(r"^\[project\.scripts\]\s*$(.*?)(?=^\[|\Z)", re.M | re.S)
_SCRIPT_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9._-]+)\s*=\s*["\']([^"\']+)["\']', re.M)

#: The modules whose job is to read or demonstrate an argparse parser.
_MAY_IMPORT_ARGPARSE = {
    "sprezzature_cli_gui/adapters/argparse.py",
    "sprezzature_cli_gui/schema.py",
    "sprezzature_cli_gui/loader.py",
    # Builds the small demonstration parser behind GET /v1/example.
    "sprezzature_cli_gui/api.py",
}


def _console_scripts() -> dict[str, str]:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = _SCRIPTS_SECTION_RE.search(text)
    assert section is not None, "pyproject.toml has no [project.scripts]"
    return dict(_SCRIPT_ENTRY_RE.findall(section.group(1)))


def test_there_are_console_scripts_to_check() -> None:
    """A regex that stopped matching would make the next test pass on nothing."""
    assert len(_console_scripts()) >= 3


@pytest.mark.parametrize("name,target", sorted(_console_scripts().items()))
def test_console_script_answers_help_like_click(name: str, target: str) -> None:
    """``--help`` exits 0 and prints click's ``Usage:``, not argparse's ``usage:``."""
    module, _, attr = target.partition(":")
    code = f"import sys; from {module} import {attr} as m; sys.argv = [{name!r}, '--help']; m()"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, f"{name} --help exited {proc.returncode}: {proc.stderr}"
    assert proc.stdout.startswith(f"Usage: {name} "), (
        f"{name} --help does not print a click usage line:\n{proc.stdout[:200]}"
    )


def _imports_argparse(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == "argparse" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "argparse" and node.level == 0:
            return True
    return False


def test_only_the_parser_readers_import_argparse() -> None:
    """A real ``import argparse`` outside the readers is a command line that grew back."""
    offenders = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for folder in ("sprezzature_cli_gui", "scripts")
        for path in (REPO_ROOT / folder).rglob("*.py")
        if _imports_argparse(path)
        and path.relative_to(REPO_ROOT).as_posix() not in _MAY_IMPORT_ARGPARSE
    )
    assert offenders == [], f"argparse imported outside the parser readers: {offenders}"


def test_the_allow_list_is_not_stale() -> None:
    """Every allow-listed module exists and still imports argparse."""
    for rel in sorted(_MAY_IMPORT_ARGPARSE):
        assert _imports_argparse(REPO_ROOT / rel), f"{rel} no longer needs its exemption"


@pytest.mark.parametrize("flag", ["-V", "--version"])
def test_the_front_door_answers_both_version_flags(flag: str) -> None:
    """``-V`` as well as ``--version``, like every other brick's front door."""
    from importlib.metadata import version

    from click.testing import CliRunner

    from sprezzature_cli_gui.cli import main

    result = CliRunner().invoke(main, [flag])
    assert result.exit_code == 0, result.output
    assert version("sprezzature-cli-gui") in result.output
