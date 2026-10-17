"""
The audit half, tested against the ways a page actually drifts.

This brick's promise is narrow and checkable: every sub-command and every
flag of a command-line tool becomes a form field. The failure mode is quiet —
a regenerated page that dropped an option still renders, still builds valid
shell, and still looks finished. Nobody finds out until someone needs the
option that went missing.

So each test below is a drift, not a shape check: a flag removed, a field
left behind pointing at an option the parser no longer accepts, a choice list
that lost an entry, a program name that stopped matching what the tool is
installed as. A healthy page must produce nothing, or the suite is measuring
its own fixtures.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse

import pytest

from sprezzature_cli_gui.audit import audit
from sprezzature_cli_gui.renderer import render_html
from sprezzature_cli_gui.schema import walk


def _parser() -> argparse.ArgumentParser:
    """A tool with one of everything the audit reasons about."""
    parser = argparse.ArgumentParser(prog="demo", description="a demo tool")
    parser.add_argument("src")
    parser.add_argument("--kind", choices=["informative", "decorative"], default="informative")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--verbose", action="store_true")
    subs = parser.add_subparsers(dest="cmd")
    nested = subs.add_parser("publish", help="ship it")
    nested.add_argument("--dry-run", action="store_true")
    return parser


@pytest.fixture
def tree() -> dict:
    return walk(_parser())


@pytest.fixture
def page(tree: dict) -> str:
    return render_html(tree)


def test_a_page_generated_from_the_parser_is_clean(tree: dict, page: str) -> None:
    """
    The baseline, without which every other test here proves nothing.

    If a freshly generated page reported findings, the audit would be
    measuring the renderer's style rather than the drift between two
    artefacts.
    """
    assert audit(tree, page) == []


def test_a_flag_the_page_lost_is_reported(tree: dict, page: str) -> None:
    """The core promise: an option the GUI cannot reach."""
    broken = page.replace('data-cli-flag="--count"', 'data-cli-flag="--kount"')
    rules = {f.rule for f in audit(tree, broken)}
    assert "flag-not-in-page" in rules


def test_a_field_building_an_unknown_flag_is_reported(tree: dict, page: str) -> None:
    """
    The opposite drift, and the one that fails at run time.

    A field left behind after a flag was renamed assembles a command line the
    tool rejects — the user clicks copy, pastes, and gets an error about an
    option they never chose.
    """
    broken = page.replace('data-cli-flag="--count"', 'data-cli-flag="--kount"')
    offenders = [f.subject for f in audit(tree, broken) if f.rule == "field-has-no-flag"]
    assert offenders == ["--kount"]


def test_a_sub_command_flag_is_covered_too(tree: dict, page: str) -> None:
    """
    Sub-commands are where a walker most often stops early.

    The flag below only exists under `publish`; an audit that only looked at
    the root would call this page complete.
    """
    assert 'data-cli-flag="--dry-run"' in page
    broken = page.replace('data-cli-flag="--dry-run"', 'data-cli-flag="--x"')
    subjects = {f.subject for f in audit(tree, broken) if f.rule == "flag-not-in-page"}
    assert any("--dry-run" in s for s in subjects), subjects


def test_a_dropped_choice_is_reported(tree: dict, page: str) -> None:
    """
    A narrowed dropdown is invisible: the control still works.

    The user simply cannot pick a value the tool accepts, and nothing on the
    page suggests the list is short.
    """
    broken = page.replace('value="decorative"', 'value="decoratif"')
    findings = [f for f in audit(tree, broken) if f.rule == "choice-dropped"]
    assert findings
    assert "decorative" in findings[0].message


def test_a_positional_is_covered(tree: dict, page: str) -> None:
    """A positional has no flag, and is just as easy to drop."""
    broken = page.replace('data-cli-flag="src"', 'data-cli-flag="source"')
    rules = {f.rule for f in audit(tree, broken)}
    assert "flag-not-in-page" in rules


def test_a_program_name_that_stopped_matching_is_reported(tree: dict, page: str) -> None:
    """
    The trap `schema.walk` already documents, now caught rather than noted.

    A Click group reports its decorated function's name — usually `main` —
    which is rarely the installed console-script name. The page then builds a
    command line that does not exist, and it looks perfectly plausible.
    """
    findings = audit({**tree, "prog": "sprezzature-demo"}, page)
    assert [f.rule for f in findings] == ["prog-mismatch"]
    assert "demo" in findings[0].message


def test_a_page_with_no_command_seed_is_reported(tree: dict, page: str) -> None:
    """Without the seed, the copy button hands over a bare flag list."""
    broken = page.replace("const parts = ['demo']", "const parts = []")
    assert "prog-missing" in {f.rule for f in audit(tree, broken)}


def test_findings_say_what_breaks_not_just_what_differs(tree: dict, page: str) -> None:
    """
    Every message names the consequence.

    An audit that says "mismatch" sends the reader back to diff two files. The
    point of these rules is that each one already knows why it matters.
    """
    broken = page.replace('data-cli-flag="--count"', 'data-cli-flag="--kount"')
    for finding in audit(tree, broken):
        assert len(finding.message.split()) >= 8, finding
