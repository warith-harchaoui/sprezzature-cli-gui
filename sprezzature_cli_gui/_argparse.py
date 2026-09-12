"""
_argparse
=========

A shared factory for this skill's command-line parsers.

``make_parser(prog, description, epilog=None)`` returns an ``ArgumentParser``
(the standard-library object that reads a command's flags and arguments),
already set up the way every script in this skill expects:

- ``prog`` is set explicitly, so ``--help`` prints a clean tool name instead
  of the full script path.
- ``RawDescriptionHelpFormatter`` is used, so a multi-line description or
  ``epilog`` is printed exactly as written instead of being rewrapped.
- A standard ``-V`` / ``--version`` flag is added automatically.

This file is deliberately duplicated, byte for byte, across every
``sprezzature-*`` skill (for example ``sprezzature-colors/scripts/_argparse.py``)
so that each skill stays self-contained and installable on its own, with no
shared dependency between skills. Because it is a duplicate, not a shared
import, a change here has to be copied by hand into every sibling copy, and
``SKILL_VERSION`` bumped in each one at release time; ``release.sh`` checks
that the copies have not drifted apart.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse

SKILL_VERSION = "1.0.0"


def make_parser(
    prog: str,
    description: str,
    epilog: str | None = None,
) -> argparse.ArgumentParser:
    """Build a pre-configured argparse parser.

    Parameters
    ----------
    prog : str
        Program name shown in ``--help`` (e.g. ``"sprezzature-figures-make"``).
    description : str
        One-paragraph description shown above the options table.
    epilog : str or None, optional
        Text shown below the options table, usually usage examples.

    Returns
    -------
    argparse.ArgumentParser
        Parser with ``-V``/``--version`` pre-attached.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {SKILL_VERSION}",
    )
    return parser
