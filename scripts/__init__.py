"""
sprezzature_cli_gui
=============

The real code behind the ``cli_to_gui`` skill, split into one module per
concern. The single file ``cli_to_gui.py`` still exists and still works
exactly as before; it now just re-exports what lives here, rather than
containing all the code itself:

- :mod:`sprezzature_cli_gui.loader`: turns a ``module:callable`` spec (a
  string such as ``"mypkg.cli:build_parser"``) into the actual parser
  factory it names.
- :mod:`sprezzature_cli_gui.schema`: the shared parser-tree helpers
  (``_safe_default``, ``NO_DEFAULT``) plus the framework-dispatch entry
  point :func:`~sprezzature_cli_gui.schema.walk`.
- :mod:`sprezzature_cli_gui.adapters`: one adapter per supported source
  framework (argparse, Click, and the ``--from-help`` fallback), each
  reducing its framework's parser to the same shared dict shape.
- :mod:`sprezzature_cli_gui.renderer`: the module that turns that dict
  into the emitted HTML page.
- :mod:`sprezzature_cli_gui.cli`: the command-line entry point.

This split is purely structural: it changes where the code lives, not what
it does. No behavior and no byte of the emitted HTML changed when the
original single file was divided up this way.
"""

from __future__ import annotations
