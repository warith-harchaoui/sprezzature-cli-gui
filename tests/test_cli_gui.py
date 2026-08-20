"""End-to-end tests for sprezzature-cli-gui: that the package imports, that
its command line actually runs and prints usable ``--help`` text, and that
pointing it at a real argparse factory produces a working HTML page."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def test_import() -> None:
    """The package imports without error."""
    import sprezzature_cli_gui  # noqa: F401


def test_cli_to_gui_help() -> None:
    """cli_to_gui --help exits 0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "cli_to_gui.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        "spec" in result.stdout.lower()
        or "parser" in result.stdout.lower()
        or "gui" in result.stdout.lower()
    )


def test_generate_gui_from_argparse_spec() -> None:
    """Generating a GUI from a simple argparse spec produces HTML output."""
    import sys
    import tempfile
    import textwrap
    from pathlib import Path

    # Write a tiny CLI factory to a temp file
    spec_src = textwrap.dedent("""\
        import argparse
        def make_parser():
            p = argparse.ArgumentParser(prog="demo", description="Demo CLI")
            p.add_argument("--name", default="world", help="Name to greet")
            p.add_argument("--count", type=int, default=1, help="Times to greet")
            return p
    """)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(spec_src)
        tmp_spec = Path(f.name)

    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "cli_to_gui.py"), f"{tmp_spec}:make_parser"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "<!DOCTYPE html>" in result.stdout or "<html" in result.stdout
        assert "demo" in result.stdout.lower() or "Demo CLI" in result.stdout
    finally:
        tmp_spec.unlink(missing_ok=True)
