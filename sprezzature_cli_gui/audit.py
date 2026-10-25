"""
The audit half: does the page you emitted still cover the CLI it came from?

This brick makes one promise — point it at a command-line tool and get back a
page where every sub-command and every flag is a form field. Nothing checked
that the promise held. A page that silently drops a flag looks entirely
correct: the form renders, the fields work, the built command line is valid
shell. It is simply missing an option the tool accepts, and nobody notices
until someone needs that option and cannot find it.

The gap is not hypothetical in shape. A GUI is regenerated when its CLI
changes, and the regeneration is the moment a flag goes missing — a renamed
`dest`, a sub-command the adapter walked past, a choice list that lost an
entry. The source of truth (the parser) and the artefact (the HTML) are both
right there, so the check is a comparison, not a judgement:

* every action in the parser tree has a field in the page — **coverage**;
* every field in the page maps to an action the parser accepts — **no
  phantoms**, because a field that builds an unknown flag produces a command
  line that fails at run time;
* every choice survives — a dropped entry narrows what the user can pick,
  invisibly;
* the page builds a command line that starts with the name the tool is
  actually installed as.

Static, offline, no browser: both inputs are already in hand.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import html as html_module
import re
from dataclasses import dataclass
from typing import Any

#: Every field the renderer emits carries the flag it builds, which is what
#: makes this comparison exact rather than a guess at labels.
_FLAG_RE = re.compile(r'data-cli-flag="([^"]*)"')

#: Options inside a rendered ``<select>``.
_OPTION_RE = re.compile(r"<option[^>]*value=\"([^\"]*)\"")

#: The line in the emitted script that seeds the built command line. Matched
#: here rather than on the visible ``<h1>``: the heading is decoration, this
#: is the string the page actually types for the user, and they can differ.
_PROG_RE = re.compile(r"const parts = \['([^']*)'\]")


@dataclass(frozen=True)
class Finding:
    """One way the page and the parser disagree."""

    rule: str
    subject: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.subject} — {self.message}"


def _identity(action: dict[str, Any]) -> str:
    """What the renderer will stamp into ``data-cli-flag`` for this action.

    An option is identified by its first long flag; a positional has no flag
    and is identified by its ``dest``, which is what the renderer uses too.
    """
    flags = action.get("flags") or []
    return flags[0] if flags else str(action.get("dest", ""))


def _actions(tree: dict[str, Any], path: str = "") -> list[tuple[str, dict]]:
    """Every action in the tree, including sub-commands, with its path."""
    out: list[tuple[str, dict]] = []
    for action in tree.get("actions") or []:
        out.append((path, action))
    subs = tree.get("sub_commands") or {}
    items = subs.items() if isinstance(subs, dict) else [(s, s) for s in subs]
    for name, sub in items:
        if isinstance(sub, dict):
            out.extend(_actions(sub, f"{path}{name} " if path else f"{name} "))
    return out


def audit(tree: dict[str, Any], page: str) -> list[Finding]:
    """
    Compare a parser tree against the page rendered from it.

    Parameters
    ----------
    tree : dict
        The canonical tree from :func:`sprezzature_cli_gui.schema.walk`.
    page : str
        The HTML :func:`sprezzature_cli_gui.renderer.render_html` produced.

    Returns
    -------
    list of Finding
        Empty when the page covers the CLI exactly.
    """
    findings: list[Finding] = []
    emitted = set(_FLAG_RE.findall(page))

    # ── coverage ────────────────────────────────────────────────────────
    for path, action in _actions(tree):
        identity = _identity(action)
        if not identity:
            continue
        if identity not in emitted:
            where = f"{path}{identity}".strip()
            findings.append(
                Finding(
                    rule="flag-not-in-page",
                    subject=where,
                    message=(
                        "the parser accepts it and the page offers no field for "
                        "it, so a user of the GUI cannot reach this option at all"
                    ),
                )
            )

    # ── no phantoms ─────────────────────────────────────────────────────
    known = {_identity(a) for _, a in _actions(tree)} - {""}
    for flag in sorted(emitted - known):
        findings.append(
            Finding(
                rule="field-has-no-flag",
                subject=flag,
                message=(
                    "the page builds this into the command line and the parser "
                    "does not accept it; the command it assembles will fail"
                ),
            )
        )

    # ── choices survive ─────────────────────────────────────────────────
    options_in_page = set(html_module.unescape(value) for value in _OPTION_RE.findall(page))
    for path, action in _actions(tree):
        choices = action.get("choices") or []
        if not choices:
            continue
        missing = [str(c) for c in choices if str(c) not in options_in_page]
        if missing:
            findings.append(
                Finding(
                    rule="choice-dropped",
                    subject=f"{path}{_identity(action)}".strip(),
                    message=(
                        f"the parser allows {sorted(str(c) for c in choices)} and "
                        f"the page omits {missing}, which narrows what a user can "
                        f"pick without saying so"
                    ),
                )
            )

    # ── the command line it builds is the one that exists ───────────────
    prog = str(tree.get("prog") or "")
    if prog:
        stamped = _PROG_RE.findall(page)
        if not stamped:
            findings.append(
                Finding(
                    rule="prog-missing",
                    subject=prog,
                    message=(
                        "the page carries no seed for the command line it builds, "
                        "so the copy button would hand the user a bare flag list"
                    ),
                )
            )
        elif prog not in stamped:
            findings.append(
                Finding(
                    rule="prog-mismatch",
                    subject=prog,
                    message=(
                        f"the page builds a command line starting with "
                        f"{stamped[0]!r}; a Click group's name defaults to the "
                        f"decorated function (often `main`), which is rarely the "
                        f"installed console-script name, so the page would hand "
                        f"the user a command that does not exist"
                    ),
                )
            )

    return findings
