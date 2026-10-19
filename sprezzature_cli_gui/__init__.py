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

Two functions, and the split between them is a security boundary
-----------------------------------------------------------------
:func:`~sprezzature_cli_gui.schema.walk` reads a parser **in your process** and
returns a plain JSON tree. :func:`~sprezzature_cli_gui.renderer.render_html`
turns such a tree into the page. They are separate because the first one has
to import your module and call your factory, and the second one does not.

That is why the HTTP surface accepts a tree and refuses a ``module:factory``
spec: importing an arbitrary module named by an unauthenticated caller is
remote code execution, and no allow-list makes it safe enough to be worth it.
The refusal is only honest if the library it points at exists — so these two
names are the package's first-class interface, not an implementation detail::

    from sprezzature_cli_gui import walk, render_html

    tree = walk(build_parser())          # in your process, with your module
    open("gui.html", "w").write(render_html(tree))

Usage example
-------------
>>> import argparse
>>> from sprezzature_cli_gui import walk
>>> parser = argparse.ArgumentParser(prog="greet")
>>> _ = parser.add_argument("--name", help="who to greet")
>>> tree = walk(parser)
>>> tree["prog"]
'greet'
"""

__version__ = "1.1.0"
__author__ = "Warith HARCHAOUI"
__email__ = "warithmetics@deraison.ai"
__license__ = "BSD-3-Clause"

from sprezzature_cli_gui.audit import Finding, audit
from sprezzature_cli_gui.renderer import render_html
from sprezzature_cli_gui.schema import walk

__all__ = [
    # the two halves of the job
    "walk",
    "render_html",
    # and the check that they agree
    "audit",
    "Finding",
    "__version__",
]
