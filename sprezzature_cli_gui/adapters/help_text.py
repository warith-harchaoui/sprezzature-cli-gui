"""
sprezzature_cli_gui.adapters.help_text
===============================

The fallback adapter: reads a CLI's printed ``--help`` text instead of its
parser object, so it works even when no parser object is reachable at all.

The other adapters need a live Python object to read (an
``ArgumentParser`` or a ``Click`` command); this one needs only a command
that can be run and that prints a normal help screen when given
``--help``. That covers Python tools built with argparse, Click, or Typer,
but also non-Python ones (Rust's `clap`, Go's `cobra`, Node's
`commander`), and even a hand-written shell script, as long as it follows
the usual help-text conventions.

The trade-off is precision: help text is meant for a person to read, not a
program to parse, so this adapter recovers less detail than reading a real
parser object would. Every flag becomes a plain text field by default;
only when the help line spells out a default value (``[default: …]``), a
fixed set of choices (``[choices]``), or a recognisable placeholder name
(a METAVAR, the capitalised word standing in for the argument's value, such
as ``FILE`` in ``--input FILE``) does the adapter recover that extra
structure. The regular expressions in this module exist to recognise the
section headings and line shapes that argparse, Click, and their peers
converge on in practice.

Author
------
`Warith Harchaoui, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

#: Subprocess timeout (seconds) for the ``--help`` invocation. Long
#: enough for a slow JIT-warm CLI, short enough that a hanging
#: subprocess does not freeze the GUI generator.
HELP_TIMEOUT_S: float = 10.0


#: Section headers we recognise. Most CLI conventions converge on
#: these: argparse, Click, clap (Rust), cobra (Go), commander (Node)
#: all use some variation. We match case-insensitively, tolerate a
#: missing trailing colon (cobra favors bare all-caps headers, e.g.
#: GitHub's own ``gh`` prints ``USAGE`` and ``FLAGS`` with none), and
#: tolerate a qualifier word in front (``Global Options``, ``Common
#: Commands``, ``GitHub Actions Commands`` all show up in real cobra
#: output, not just the bare word).
RE_OPTIONS_HEADER: re.Pattern[str] = re.compile(
    r"^\s*(?:[a-z]+\s+)*?(options|optional arguments|flags)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
RE_COMMANDS_HEADER: re.Pattern[str] = re.compile(
    r"^\s*(?:[a-z]+\s+)*?(commands|sub-?commands|available commands)\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
RE_USAGE_HEADER: re.Pattern[str] = re.compile(
    r"^\s*usage\s*:?[ \t]*(.*)$",
    re.IGNORECASE | re.MULTILINE,
)
RE_POSITIONAL_HEADER: re.Pattern[str] = re.compile(
    r"^\s*(positional arguments|arguments):\s*$",
    re.IGNORECASE | re.MULTILINE,
)

#: Line shape for one option entry: leading whitespace, one or more
#: ``-flag`` tokens (optionally with a comma-list and an inline
#: METAVAR), then 2+ whitespace and the help text.
#:
#: Permissive on purpose: argparse, Click, clap, cobra, commander
#: each format option lines slightly differently and we want all of
#: them to land in the same parse. The flag-token split happens
#: after the match, in :func:`_parse_option_line`.
#:
#: Captures:
#:   1. flags-and-metavar fragment (e.g. ``"-V, --version"``,
#:      ``"--input PATH"``, ``"--format [mp3|ogg|flac]"``)
#:   2. inline help text (may be empty when help is on the next line)
RE_OPTION_LINE: re.Pattern[str] = re.compile(
    r"^\s{2,}(-{1,2}[^\s,]+(?:,\s*-{1,2}[^\s,]+)*"
    r"(?:\s[^\s]+)?)"
    r"(?:\s{2,}(.*))?$"
)

#: One sub-command row: leading whitespace, the slug (cobra often
#: suffixes it with a colon, e.g. ``auth:``), two-or-more spaces, the
#: help fragment.
RE_COMMAND_LINE: re.Pattern[str] = re.compile(
    r"^\s{2,}([a-z0-9][a-z0-9_-]*):?(?:\s{2,}(.*))?$",
    re.IGNORECASE,
)

#: ``[default: 128]`` / ``[default=128]`` / ``(default: 128)``:
#: extracts the literal default the help text advertised.
RE_DEFAULT_HINT: re.Pattern[str] = re.compile(
    r"[\[\(]default[:= ]\s*([^\]\)]+)[\]\)]",
    re.IGNORECASE,
)
RE_REQUIRED_HINT: re.Pattern[str] = re.compile(
    r"\[required\]|\(required\)",
    re.IGNORECASE,
)
#: ``[mp3|ogg|flac]`` or ``{mp3,ogg,flac}``: Click vs argparse styles.
RE_CHOICE_HINT: re.Pattern[str] = re.compile(r"\[([^\[\]]+\|[^\[\]]+)\]|\{([^{}]+,[^{}]+)\}")


def _run_help(cmdline: str) -> str:
    """
    Run ``<cmdline> --help`` and return its stdout.

    Parameters
    ----------
    cmdline : str
        The command to introspect, as a shell string. Split on
        whitespace; we never invoke the shell itself to keep
        injection surface narrow.

    Returns
    -------
    str
        Captured stdout. Stderr is folded in too because some CLIs
        (notably older argparse) write help to stderr.

    Raises
    ------
    FileNotFoundError
        If the command does not resolve on ``$PATH``.
    subprocess.TimeoutExpired
        If ``--help`` does not return within
        :data:`HELP_TIMEOUT_S` seconds.
    """
    import shlex
    import subprocess as sp

    parts: list[str] = shlex.split(cmdline) + ["--help"]
    proc = sp.run(
        parts,
        capture_output=True,
        text=True,
        timeout=HELP_TIMEOUT_S,
        check=False,
    )
    # Many CLIs exit non-zero on ``--help`` (notably tools that
    # treat help as "no real command was named"). Trust the output,
    # not the exit code.
    return proc.stdout + ("\n" + proc.stderr if proc.stderr else "")


def _usage_synopsis(help_text: str, usage_match: re.Match[str]) -> str:
    """
    Return the actual usage line's text, wherever it lives.

    Most conventions (argparse, Click, clap) put it right after the
    ``usage:`` token on the same line. Cobra's own help (``gh``, most
    Go CLIs built on it) instead prints a bare ``USAGE`` header and puts
    the real synopsis on the next line indented underneath it. Both
    shapes end up here as one string.
    """
    inline: str = usage_match.group(1).strip()
    if inline:
        return inline
    following: list[str] = help_text[usage_match.end() :].splitlines()
    return following[0].strip() if following else ""


def _usage_block_end(help_text: str, usage_match: re.Match[str]) -> int:
    """
    Return the offset just past the whole usage block.

    A usage block can span more than one physical line: a header-only
    style (``USAGE`` on its own line, synopsis on the next) needs one
    extra line consumed, and some CLIs (``cargo``) print several
    alternate invocations stacked under one ``Usage:`` line. Either
    way, the block ends at the first blank line.
    """
    start: int = usage_match.end()
    consumed = 0
    for line in help_text[start:].splitlines(keepends=True):
        if not line.strip():
            break
        consumed += len(line)
    return start + consumed


def _extract_prog(cmdline: str, help_text: str = "") -> str:
    """
    Best-effort program name.

    Prefers the ``usage: <prog> …`` line in the help output (the CLI's
    own opinion of its prog name); falls back to the basename of the
    first shell token. Shell wrappers like ``python3 myscript.py`` get
    correctly identified by the usage line as ``myscript``, not
    ``python3``.
    """
    if help_text:
        m = RE_USAGE_HEADER.search(help_text)
        if m:
            usage_line: str = _usage_synopsis(help_text, m)
            first_token: str = usage_line.split()[0] if usage_line else ""
            if first_token:
                return first_token
    import shlex

    parts: list[str] = shlex.split(cmdline) if cmdline else []
    # Skip leading interpreter / wrapper tokens to land on the real
    # script name when invoked as ``python3 path/to/script.py``.
    for token in parts:
        name: str = Path(token).name
        if (
            name
            and not name.startswith("-")
            and name
            not in {
                "python",
                "python3",
                "python2",
                "uvx",
                "uv",
                "npx",
                "node",
                "ruby",
                "perl",
                "bash",
                "sh",
            }
        ):
            # Strip a ``.py`` / ``.js`` / ``.rb`` extension so the GUI
            # title is the conventional command name.
            return Path(name).stem or name
    return parts[0] if parts else "cli"


#: argparse-style sub-command list: ``{cmd1,cmd2,cmd3}`` on a single
#: indented line under ``positional arguments:``.
RE_ARGPARSE_SUBS: re.Pattern[str] = re.compile(
    r"^\s{2,}\{([a-z0-9][a-z0-9_,-]*)\}\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _section(text: str, header_re: re.Pattern[str]) -> str | None:
    """
    Return the lines under every occurrence of ``header_re``, joined.

    Returns ``None`` if the header never appears in ``text``. Cobra
    CLIs routinely split one logical section across several named
    groups (``gh --help`` prints ``CORE COMMANDS``, ``GITHUB ACTIONS
    COMMANDS``, ``ALIAS COMMANDS`` and ``ADDITIONAL COMMANDS`` as four
    separate blocks, none of them called just "commands"); collecting
    every match, not only the first, is what makes those CLIs' full
    sub-command list show up instead of just the first group.

    Each individual block ends at the first line that does not start
    with two or more spaces; that is how argparse / Click / cobra all
    visually delimit one section from the next.
    """
    blocks: list[str] = []
    for m in header_re.finditer(text):
        start: int = m.end()
        lines: list[str] = text[start:].splitlines()
        out: list[str] = []
        for line in lines:
            if not line.strip():
                # A blank line is permitted *between* entries; we keep
                # going until two consecutive blanks OR an outdented line.
                out.append(line)
                continue
            if not line.startswith(" "):
                break
            out.append(line)
        blocks.append("\n".join(out))
    return "\n".join(blocks) if blocks else None


def _parse_option_line(line: str, help_continuation: str = "") -> dict[str, Any] | None:
    """Project one help-text option line into the canonical action dict."""
    m = RE_OPTION_LINE.match(line)
    if not m:
        return None
    flags_fragment: str = m.group(1).strip()
    inline_help: str = (m.group(2) or "").strip()
    full_help: str = (inline_help + " " + help_continuation).strip()

    # Split ``"-V, --version"`` → ``["-V", "--version"]``. clap marks a
    # repeatable flag with a trailing ellipsis (``-v, --verbose...``);
    # strip it so it doesn't end up baked into the dest/flag name.
    flag_tokens: list[str] = []
    for piece in flags_fragment.split(","):
        token: str = piece.strip().split()[0] if piece.strip() else ""
        if token.endswith("..."):
            token = token[:-3]
        if token.startswith("-"):
            flag_tokens.append(token)
    if not flag_tokens:
        return None
    if any(t in ("-h", "--help") for t in flag_tokens):
        return None  # filter the omnipresent help line

    # ``--input PATH`` → metavar = "PATH". Lower-cased becomes our
    # candidate dest. If no metavar is present, fall back to the
    # longest flag with its leading dashes stripped.
    metavar: str | None = None
    after_flags: str = flags_fragment.split()[-1] if " " in flags_fragment else ""
    if after_flags and not after_flags.startswith("-") and after_flags not in flag_tokens:
        # Strip whichever bracket style wraps it: "<CODE>" (clap),
        # "[FILE]" (argparse optionals), "(PATH)". strip() removes any
        # of these characters from both ends, so a mismatched pair
        # (the "<" without its ">" showing up alone) is handled too.
        metavar = after_flags.strip("[]<>()")

    longest: str = max(flag_tokens, key=len)
    dest: str = longest.lstrip("-").replace("-", "_")

    # Heuristic kind detection from help text + metavar.
    kind: str = "text"
    if metavar and metavar.upper() in ("INTEGER", "INT", "N"):
        kind = "int"
    elif metavar and metavar.upper() in ("FLOAT", "NUMBER"):
        kind = "float"
    elif metavar and metavar.upper() in ("PATH", "FILE", "FILENAME", "DIR"):
        kind = "file"
    elif not metavar:
        # No metavar usually means a boolean flag.
        kind = "bool"

    # Choices: ``[mp3|ogg|flac]`` or ``{mp3,ogg,flac}``.
    choices: list[str] | None = None
    cm = RE_CHOICE_HINT.search(flags_fragment + " " + full_help)
    if cm:
        raw: str = cm.group(1) or cm.group(2) or ""
        sep: str = "|" if "|" in raw else ","
        choices = [c.strip() for c in raw.split(sep) if c.strip()]
        if choices:
            kind = "choice"

    # Default: ``[default: 128]`` (Click) or ``(default: 128)`` (argparse).
    default: Any = None
    dm = RE_DEFAULT_HINT.search(full_help)
    if dm:
        raw_default: str = dm.group(1).strip()
        # Try int / float, fall back to string.
        try:
            default = int(raw_default)
        except ValueError:
            try:
                default = float(raw_default)
            except ValueError:
                default = raw_default

    required: bool = bool(RE_REQUIRED_HINT.search(full_help))

    return {
        "dest": dest,
        "flags": flag_tokens,
        "kind": kind,
        "choices": choices,
        "required": required,
        "default": default,
        "help": full_help,
        "nargs": None,
        "metavar": metavar,
    }


def _parse_options_section(section: str | None) -> list[dict[str, Any]]:
    """Walk an options section and produce one action dict per entry.

    A help line that wraps onto more than one following indented line
    (help text several sentences long) accumulates every continuation
    line, not just the first: the previous shape here dropped every
    continuation past the first one silently.
    """
    if not section:
        return []
    out: list[dict[str, Any]] = []
    pending_line: str | None = None
    pending_continuation: list[str] = []

    def flush() -> None:
        """Parse and emit the buffered option line plus its continuation, if any."""
        nonlocal pending_line, pending_continuation
        if pending_line is not None:
            parsed = _parse_option_line(pending_line, " ".join(pending_continuation))
            if parsed:
                out.append(parsed)
        pending_line = None
        pending_continuation = []

    for line in section.splitlines():
        if not line.strip():
            flush()
            continue
        # An indented line that does NOT start with ``-`` (under deep
        # indent) is a help-text continuation for the previous option;
        # it accumulates rather than replacing what came before.
        stripped: str = line.lstrip()
        if pending_line is not None and not stripped.startswith("-"):
            pending_continuation.append(stripped)
            continue
        flush()
        pending_line = line
    flush()
    return out


def _parse_commands_section(section: str | None) -> list[tuple[str, str]]:
    """Yield (sub_command_name, short_help) from a Commands section.

    ``section`` may be several command-group blocks concatenated (see
    :func:`_section`): cobra CLIs list the same command family under
    more than one heading (e.g. one curated "Common Commands" summary
    plus the exhaustive "Commands" list further down), so the same
    name can legitimately appear twice. Kept to the first sighting
    only, both to avoid a duplicate recursive ``--help`` call per
    repeat and to keep whichever short-help text showed up first.
    """
    if not section:
        return []
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in section.splitlines():
        m = RE_COMMAND_LINE.match(line)
        if not m:
            continue
        name: str = m.group(1)
        help_text: str = (m.group(2) or "").strip()
        # Reject false matches that look like option lines.
        if name.startswith("-") or name in seen:
            continue
        seen.add(name)
        out.append((name, help_text))
    return out


def walk_from_help(
    cmdline: str,
    *,
    _depth: int = 0,
    _max_depth: int = 3,
) -> dict[str, Any]:
    """
    Parse ``<cmdline> --help`` into the canonical parser tree.

    Works on any CLI that emits a conventional help block:
    argparse, Click, Typer, clap (Rust), cobra (Go), commander
    (Node), even hand-rolled shell scripts that follow the
    standard sections. Lower fidelity than native introspection
    (everything maps to ``"text"`` unless a ``[default: …]``,
    ``[choices]`` or recognised METAVAR is visible).

    Parameters
    ----------
    cmdline : str
        The command to introspect (passed through :mod:`shlex.split`
        (never via the shell, to keep the injection surface narrow).
    _depth : int, default 0
        Internal: current recursion depth into sub-commands.
    _max_depth : int, default 3
        Internal: stop recursing into sub-commands past this many
        levels. Defends against pathological CLIs whose sub-command
        list includes itself.

    Returns
    -------
    dict
        Canonical parser tree.
    """
    help_text: str = _run_help(cmdline)
    description: str = ""
    usage_match = RE_USAGE_HEADER.search(help_text)
    if usage_match:
        # Two conventions show up in practice: argparse/Click print the
        # one-line synopsis *after* the usage block; clap prints it
        # *before* (e.g. "Rust's package manager" ahead of cargo's own
        # "Usage: cargo ..."). Prefer whatever prose precedes the usage
        # block when there is any, since that is never itself part of
        # the block; fall back to the prose that follows it otherwise.
        before_usage: str = help_text[: usage_match.start()].strip()
        after_usage: int = _usage_block_end(help_text, usage_match)
        # Treat any prose between the Usage block and the first
        # ``Options:`` / ``Commands:`` header as the fallback description.
        next_header = min(
            (
                m.start()
                for m in [
                    RE_OPTIONS_HEADER.search(help_text, after_usage),
                    RE_COMMANDS_HEADER.search(help_text, after_usage),
                    RE_POSITIONAL_HEADER.search(help_text, after_usage),
                ]
                if m is not None
            ),
            default=len(help_text),
        )
        after_text: str = help_text[after_usage:next_header].strip()
        description = before_usage or after_text

    options: list[dict[str, Any]] = _parse_options_section(_section(help_text, RE_OPTIONS_HEADER))
    positionals: list[dict[str, Any]] = _parse_options_section(
        _section(help_text, RE_POSITIONAL_HEADER)
    )
    commands_raw: list[tuple[str, str]] = _parse_commands_section(
        _section(help_text, RE_COMMANDS_HEADER)
    )
    # argparse uses ``positional arguments:`` + a ``{cmd1,cmd2}`` line
    # to list sub-commands. Detect that shape and fold its entries
    # into the same sub_commands recursion.
    for m in RE_ARGPARSE_SUBS.finditer(help_text):
        for name in m.group(1).split(","):
            name = name.strip()
            if name and not any(c[0] == name for c in commands_raw):
                commands_raw.append((name, ""))

    sub_commands: dict[str, dict[str, Any]] = {}
    if _depth < _max_depth:
        for name, _ in commands_raw:
            try:
                sub_commands[name] = walk_from_help(
                    f"{cmdline} {name}",
                    _depth=_depth + 1,
                    _max_depth=_max_depth,
                )
            except (FileNotFoundError, OSError):
                # The sub-command exists in the help text but cannot
                # be invoked. Skip rather than abort the whole walk.
                continue
            except Exception:  # noqa: BLE001 (best-effort)
                continue

    return {
        "prog": _extract_prog(cmdline, help_text),
        "description": description,
        "actions": options + positionals,
        "sub_commands": sub_commands,
    }
