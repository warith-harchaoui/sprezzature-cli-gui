"""
A spec that does not work is one sentence on stderr, on both front doors.

The README promises that a spec which cannot be found, imported or walked
exits 1 with one sentence. The generator kept the promise for four exception
types and the audit for none of them, and neither kept it for a target whose
own code raised at import, or for ``--from-help`` given a command it could not
split or that never answered. All of those printed a traceback through this
package, which reads as this package having crashed.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from sprezzature_cli_gui.adapters import help_text

GENERATOR = "sprezzature_cli_gui.cli"
AUDIT = "sprezzature_cli_gui.audit_cli"


def _run(module: str, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one of the two commands the way a shell does."""
    return subprocess.run(
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


def _assert_one_sentence(done: subprocess.CompletedProcess[str], expected: str) -> None:
    """Exit 1, the expected words, and no traceback."""
    assert done.returncode == 1, done.stderr
    assert "Traceback" not in done.stderr, done.stderr
    assert expected in done.stderr, done.stderr


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("no_such_module_xyz:make", "No module named"),
        ("no_colon_here", "must be of the form"),
        ("./target.py:missing", "has no attribute"),
        ("./target.py:not_a_parser", "expected argparse.ArgumentParser"),
        ("./syntax_error.py:make", "SyntaxError"),
        ("./raises_on_import.py:make", "RuntimeError: boom at import"),
        ("./target.py:raises", "RuntimeError: boom in factory"),
    ],
)
@pytest.mark.parametrize("module", [GENERATOR, AUDIT])
def test_a_bad_spec_says_one_sentence(
    module: str, spec: str, expected: str, tmp_path: Path
) -> None:
    """Each way a spec fails, on the generator and on the audit."""
    (tmp_path / "target.py").write_text(
        "def not_a_parser():\n    return 3\n\n"
        "def raises():\n    raise RuntimeError('boom in factory')\n",
        encoding="utf-8",
    )
    (tmp_path / "syntax_error.py").write_text("def make(:\n", encoding="utf-8")
    (tmp_path / "raises_on_import.py").write_text(
        "raise RuntimeError('boom at import')\n", encoding="utf-8"
    )
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")

    args = [spec, str(page)] if module == AUDIT else [spec]
    _assert_one_sentence(_run(module, *args, cwd=tmp_path), expected)


def test_from_help_with_an_unbalanced_quote_says_one_sentence(tmp_path: Path) -> None:
    """``shlex`` refuses the command line before anything is run."""
    done = _run(GENERATOR, "--from-help", "tool 'unbalanced", cwd=tmp_path)
    _assert_one_sentence(done, "--from-help failed")


def test_from_help_with_a_silent_command_writes_no_page(tmp_path: Path) -> None:
    """A command that prints nothing yields a refusal, not an empty form."""
    script = tmp_path / "silent.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    script.chmod(0o755)
    out = tmp_path / "gui.html"

    done = _run(GENERATOR, "--from-help", str(script), "--out", str(out), cwd=tmp_path)

    _assert_one_sentence(done, "printed nothing")
    assert not out.exists()


def test_a_help_that_never_answers_is_an_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """The timeout arrives as the one type ``--from-help`` reports."""
    monkeypatch.setattr(help_text, "HELP_TIMEOUT_S", 0.05)
    with pytest.raises(OSError, match="did not answer"):
        help_text.walk_from_help(f"{sys.executable} -c 'import time; time.sleep(5)'")
