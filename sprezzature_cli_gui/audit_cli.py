"""
The audit command — ``sprezzature-cli-gui-audit``.

Takes the same parser spec the generator takes, plus the page it produced,
and reports where the two have drifted apart. Running it on a page you just
generated is pointless by construction; running it on a page committed last
month, against a CLI that has moved since, is the whole point.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from sprezzature_cli_gui.audit import audit
from sprezzature_cli_gui.loader import load_parser_from_spec
from sprezzature_cli_gui.schema import walk


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Check that a generated GUI still covers the command-line tool it was "
        "generated from: every flag reachable, no field building an option the "
        "parser rejects, no choice quietly dropped."
    ),
    epilog=(
        "Examples:\n\n"
        "  \b\n"
        "  sprezzature-cli-gui-audit mytool.cli:build_parser gui.html\n"
        "  sprezzature-cli-gui-audit pkg.mod:factory gui.html --format json\n\n"
        "Exits 1 when the page and the parser disagree, so it gates a build "
        "the way the lint half of every other brick does."
    ),
)
@click.version_option(package_name="sprezzature-cli-gui")
@click.argument("spec")
@click.argument("page", type=click.Path(path_type=Path))
@click.option(
    "--prog",
    default=None,
    help=(
        "Override the program name, as the generator's --prog does. A Click "
        "group reports its function name, which is rarely the installed "
        "console-script name."
    ),
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output shape.",
)
def main(spec: str, page: Path, prog: str | None, fmt: str) -> None:
    """Report where a generated page no longer matches its CLI."""
    if not page.is_file():
        # 2, not 1: "you pointed me at nothing" is not "the page disagrees".
        raise SystemExit(f"{page}: no such file")

    tree = walk(load_parser_from_spec(spec), prog=prog)
    findings = audit(tree, page.read_text(encoding="utf-8"))

    if fmt == "json":
        json.dump(
            {
                "findings_total": len(findings),
                "findings": [
                    {"rule": f.rule, "subject": f.subject, "message": f.message} for f in findings
                ],
            },
            sys.stdout,
            indent=2,
            ensure_ascii=False,
        )
        sys.stdout.write("\n")
    else:
        for finding in findings:
            click.echo(str(finding))
        click.echo(f"{len(findings)} finding(s)." if findings else "The page covers the CLI.")
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
