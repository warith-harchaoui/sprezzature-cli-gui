"""
The Click command line — ``sprezzature-cli-gui-click``.

The twin of :mod:`sprezzature_cli_gui.cli`: same flags, same handler, the
other parser. Both build the same namespace and hand it to the same ``main``,
so a flag cannot exist on one front door and be missing from the other.

There is a joke in shipping this, and it is the point. This package exists to
read a Click command and turn it into a form; not offering a Click front door
of its own would have been the kind of gap a reader notices before the README
does.

Click is an extra here (``[click]``), because the argparse front door needs
nothing — and that is why the import below is guarded. A command somebody's
own ``pip install`` just put on ``PATH`` should not answer a traceback about a
third-party package they never asked for.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import click
except ImportError:  # pragma: no cover - exercised by a bare install

    def main() -> None:  # type: ignore[misc]
        """Say which extra installs this command, and exit non-zero."""
        print(
            "sprezzature-cli-gui-click is built with Click, which this "
            "package installs with an extra:\n"
            "    pip install 'sprezzature-cli-gui[click]'\n"
            "The argparse front door, `sprezzature-cli-gui`, needs nothing.",
            file=sys.stderr,
        )
        sys.exit(1)
else:
    from sprezzature_cli_gui.cli import main as _run

    @click.command(
        name="sprezzature-cli-gui-click",
        context_settings={"help_option_names": ["-h", "--help"]},
        help=(
            "Introspect a Python CLI (argparse OR Click, autodetected) and "
            "emit a single-page vanilla-JS + Tailwind GUI mapping every "
            "sub-command and flag to a form field."
        ),
    )
    @click.version_option(package_name="sprezzature-cli-gui")
    @click.argument("spec")
    @click.option(
        "--from-help",
        "from_help",
        is_flag=True,
        default=False,
        help=(
            "Treat SPEC as a shell command line and parse its --help output. "
            "Works on non-Python CLIs; lower fidelity than introspection."
        ),
    )
    @click.option(
        "--out",
        type=click.Path(path_type=Path),
        default=None,
        help="Write the HTML here instead of stdout.",
    )
    @click.option("--title", default=None, help="Page <title>.")
    @click.option(
        "--prog",
        default=None,
        help=(
            "Override the program name in the page and the built command "
            "line. A Click group's name defaults to the decorated function's "
            "name, not the installed console script — pass the real one when "
            "they differ, or the page names a command that does not exist."
        ),
    )
    @click.option(
        "--json",
        "json_",
        is_flag=True,
        default=False,
        help="Emit the walked parser as JSON instead of HTML.",
    )
    def main(  # type: ignore[misc]
        spec: str,
        from_help: bool,
        out: Path | None,
        title: str | None,
        prog: str | None,
        json_: bool,
    ) -> None:
        """Dispatch to the shared handler; propagate its exit code."""
        # The same namespace the argparse front door builds, so the handler
        # cannot tell which one called it — which is the only way two front
        # doors stay honest about offering the same thing.
        raise SystemExit(
            _run_with(
                argparse.Namespace(
                    spec=spec,
                    from_help=from_help,
                    out=out,
                    title=title,
                    prog=prog,
                    json=json_,
                )
            )
        )

    def _run_with(args: argparse.Namespace) -> int:
        """Call the argparse handler with an already-parsed namespace."""
        return _run(_as_argv(args))

    def _as_argv(args: argparse.Namespace) -> list[str]:
        """Rebuild an argument vector from the namespace.

        The shared ``main`` parses its own argv rather than taking a
        namespace, so the twin hands it one back. Reconstructing is uglier
        than calling a common handler — and it is what keeps there from being
        two code paths that can disagree about what a flag means.
        """
        argv: list[str] = [args.spec]
        if args.from_help:
            argv.append("--from-help")
        if args.out is not None:
            argv += ["--out", str(args.out)]
        if args.title is not None:
            argv += ["--title", args.title]
        if args.prog is not None:
            argv += ["--prog", args.prog]
        if args.json:
            argv.append("--json")
        return argv


if __name__ == "__main__":  # pragma: no cover
    main()
