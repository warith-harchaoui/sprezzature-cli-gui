"""
sprezzature_cli_gui.adapters
=====================

One adapter per supported CLI framework: the small piece of code that knows
how to read that specific framework's parser object and reduce it to the
one shared dict shape (``prog`` / ``description`` / ``actions`` /
``sub_commands``) the HTML renderer consumes. Because every adapter ends
at the same shape, the renderer itself never needs to know or branch on
which framework produced it.

- :mod:`sprezzature_cli_gui.adapters.argparse`: reads a standard-library
  :class:`argparse.ArgumentParser`, always available since argparse ships
  with Python itself.
- :mod:`sprezzature_cli_gui.adapters.click`: reads an optional
  :class:`click.Command`; also covers Typer apps, which are built on Click
  internally.
- :mod:`sprezzature_cli_gui.adapters.help_text`: the fallback that needs no
  parser object at all, reading a CLI's printed ``--help`` text instead
  (used through ``--from-help``, at lower fidelity than the other two).
"""

from __future__ import annotations
