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

from sprezzature_cli_gui._argparse import make_parser
from sprezzature_cli_gui.audit import audit
from sprezzature_cli_gui.loader import load_parser_from_spec
from sprezzature_cli_gui.schema import walk


def main(argv: list[str] | None = None) -> int:
    """Report where a generated page no longer matches its CLI."""
    parser = make_parser(
        prog="sprezzature-cli-gui-audit",
        description=(
            "Check that a generated GUI still covers the command-line tool "
            "it was generated from: every flag reachable, no field building "
            "an option the parser rejects, no choice quietly dropped."
        ),
        epilog=(
            "Examples:\n"
            "  sprezzature-cli-gui-audit mytool.cli:build_parser gui.html\n"
            "  sprezzature-cli-gui-audit pkg.mod:factory gui.html --format json\n"
            "\n"
            "Exits 1 when the page and the parser disagree, so it gates a "
            "build the way the lint half of every other brick does.\n"
        ),
    )
    parser.add_argument(
        "spec",
        help="Parser factory, as 'path/to/cli.py:factory' or 'pkg.mod:factory'.",
    )
    parser.add_argument("page", type=Path, help="The generated HTML to check.")
    parser.add_argument(
        "--prog",
        default=None,
        help=(
            "Override the program name, as the generator's --prog does. A "
            "Click group reports its function name, which is rarely the "
            "installed console-script name."
        ),
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="Output shape (default: text).",
    )
    args = parser.parse_args(argv)

    if not args.page.is_file():
        sys.stderr.write(f"{args.page}: no such file\n")
        return 2

    tree = walk(load_parser_from_spec(args.spec), prog=args.prog)
    findings = audit(tree, args.page.read_text(encoding="utf-8"))

    if args.format == "json":
        json.dump(
            {
                "findings_total": len(findings),
                "findings": [
                    {"rule": f.rule, "subject": f.subject, "message": f.message}
                    for f in findings
                ],
            },
            sys.stdout, indent=2, ensure_ascii=False,
        )
        sys.stdout.write("\n")
    else:
        for finding in findings:
            print(finding)
        print(
            f"{len(findings)} finding(s)." if findings
            else "The page covers the CLI."
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
