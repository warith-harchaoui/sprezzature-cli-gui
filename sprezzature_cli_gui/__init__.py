"""
sprezzature-cli-gui -- auto-generate a single-file HTML GUI from any Python CLI.

Introspects argparse, Click, or Typer parsers and emits a vanilla-JS +
Tailwind page that maps every sub-command and flag to a form field.
The emitted page constructs the command string locally and displays it
ready for copy, Tauri invoke, or FastAPI SSE.
"""

__version__ = "1.0.0"
__author__ = "Warith HARCHAOUI"
__email__ = "warith.harchaoui@gmail.com"
__license__ = "BSD-3-Clause"
