"""
sprezzature-cli-gui: turn a Python command-line tool into a clickable form.

Reads the parser object a Python CLI already builds for itself, whether with
`argparse` (the standard library's tool for this), `Click`, or `Typer`, and emits a
single self-contained web page (plain JavaScript, Tailwind CSS) that maps every
sub-command and flag to a form field. The page builds the command line locally, in the
visitor's browser, and shows it ready to copy, to hand to a `Tauri invoke` call (the
bridge a desktop-app wrapper uses to run a command on the visitor's behalf), or to send
to a FastAPI server over SSE (Server-Sent Events, a simple one-way stream a server uses
to push live output back to the page).
"""

__version__ = "1.0.0"
__author__ = "Warith HARCHAOUI"
__email__ = "warith.harchaoui@gmail.com"
__license__ = "BSD-3-Clause"
