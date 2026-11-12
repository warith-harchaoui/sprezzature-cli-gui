"""
sprezzature_cli_gui.adapters.click
===========================

The `Click` adapter. `Click` is a popular third-party library for building
command-line tools, an alternative to Python's built-in `argparse`. It is a
base dependency of this package (its own commands are written in Click), so
this adapter is always available.

It walks a :class:`click.Command`, whether it is a single leaf command or a
``Group`` nesting sub-commands, into the same parser-tree dict shape the
argparse adapter produces, so the HTML renderer downstream never has to
branch on which framework built the CLI. `Typer` apps arrive here too, but
not by themselves: a `Typer` app is not a `click.Command` and exposes no
`.cli` attribute (that route was written here and does not exist on typer
0.20). `schema.walk` converts it with typer's own ``get_command`` first, and
what comes out is a Click command -- so from this adapter's point of view a
Typer app just is a Click group, once somebody has converted it. This module
is still imported lazily, only when a caller has actually handed it a Click
object.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

from typing import Any

from sprezzature_cli_gui.schema import _safe_default


def _param_type_name(param: Any) -> str:
    """The Click type name of a parameter, whichever Typer built it.

    Click and Typer up to 0.2x put a ``click.types`` instance on
    ``param.type``. Typer 0.29 vendors its own Click and gives its options a
    ``type_descriptor`` instead, with no ``type`` at all: read as before,
    every Typer app raised ``AttributeError`` (CI, 2026-11-11). The
    descriptor is mapped onto the names Click uses, so the rest of this
    adapter does not branch on the framework.
    """
    if hasattr(param, "type"):
        return getattr(param.type, "name", "") or ""
    td = getattr(param, "type_descriptor", None)
    if td is None:
        return ""
    if getattr(td, "is_choice", False):
        return "choice"
    if getattr(td, "is_file", False) or getattr(td, "is_path", False):
        return "path"
    return {"int": "integer", "float": "float", "bool": "boolean"}.get(
        str(getattr(td, "ranged_type_name", "")), ""
    )


def _param_choices(param: Any) -> Any:
    """The raw choices of a choice parameter, from Click or from Typer 0.29."""
    if hasattr(param, "type"):
        return getattr(param.type, "choices", None)
    choices = getattr(getattr(param, "type_descriptor", None), "choices", None)
    if choices is None:
        return None
    return [getattr(c, "value", c) for c in choices]


def _click_param_kind(param: Any) -> str:
    """
    Map a :class:`click.Parameter` to a form-field kind string.

    Mirrors :func:`_action_kind` but reads from Click's structured
    ``param.type`` / ``param.is_flag`` / ``param.multiple`` attributes
    instead of argparse's heuristic ``type=`` callable.

    Parameters
    ----------
    param : click.Parameter
        The Click parameter (an ``Option`` or ``Argument``).

    Returns
    -------
    str
        One of ``"bool"``, ``"count"``, ``"int"``, ``"float"``,
        ``"choice"``, ``"file"``, ``"text"``.
    """
    # ``is_flag=True`` is Click's idiomatic boolean switch (parallel
    # to argparse's ``store_true`` / ``store_false``).
    if getattr(param, "is_flag", False):
        return "bool"
    # ``count=True`` increments an int per repetition (``-vvv``). The page
    # asks for a number and repeats the flag that many times; as an ``int``
    # it built ``-v 3``, which Click rejects.
    if getattr(param, "count", False):
        return "count"
    # ``click.types.*`` are concrete instances on ``param.type``. We
    # inspect the type's ``name`` so we do not need to import the
    # ``click.types`` symbols at module load.
    type_name: str = _param_type_name(param)
    if type_name == "boolean":
        return "bool"
    if type_name in ("integer", "integer range"):
        return "int"
    if type_name in ("float", "float range"):
        return "float"
    if type_name == "choice":
        return "choice"
    if type_name in ("path", "filename", "file"):
        return "file"
    return "text"


def _click_param_choices(param: Any) -> list[str] | None:
    """Extract the choices list from a ``click.Choice`` param if present."""
    type_name: str = _param_type_name(param)
    if type_name != "choice":
        return None
    choices: Any = _param_choices(param)
    if choices is None:
        return None
    return [str(c) for c in choices]


def _serialize_click_param(param: Any) -> dict[str, Any]:
    """
    Project one :class:`click.Parameter` into the canonical action dict.

    The output schema is identical to :func:`serialize_action`:
    ``dest``, ``flags``, ``off_flags``, ``kind``, ``choices``,
    ``required``, ``default``, ``help``, ``nargs``, ``metavar``, so the
    HTML renderer never has to branch on the source framework.
    """
    # ``opts`` is the list of ``--flag`` strings for Options;
    # Arguments have no opts (positional).
    flags: list[str] = list(getattr(param, "opts", []) or [])
    # ``default`` is sometimes a callable (Click resolves it lazily).
    # We materialise + safe-serialise so the HTML emitter sees a
    # value it can write into ``value="…"``.
    default: Any = getattr(param, "default", None)
    if callable(default):
        try:
            default = default()
        except Exception:  # noqa: BLE001 (best-effort; fall back to None)
            default = None
    # Click 8.2+ uses a sentinel value (``click.core.Sentinel.UNSET``
    # or similar) for parameters with no explicit default; treat it
    # as "no default" so the HTML emitter does not stamp a literal
    # ``Sentinel.UNSET`` into the form's ``value="…"`` attribute.
    if default is not None and "Sentinel" in type(default).__name__:
        default = None
    return {
        "dest": param.name,
        "flags": flags,
        # ``--color/--no-color``: Click keeps the off spelling in
        # ``secondary_opts``. Without it the page could only ever build the on
        # spelling, so a flag defaulting to on could not be turned off.
        "off_flags": list(getattr(param, "secondary_opts", []) or []),
        "kind": _click_param_kind(param),
        "choices": _click_param_choices(param),
        "required": bool(getattr(param, "required", False)),
        "default": _safe_default(default),
        "help": (getattr(param, "help", "") or "").strip(),
        # Click uses ``nargs=-1`` for "any number"; argparse uses "*".
        # We surface Click's int directly so the HTML side can decide.
        "nargs": getattr(param, "nargs", None),
        "metavar": getattr(param, "metavar", None),
    }


def walk_click(cmd: Any, prog: str | None = None) -> dict[str, Any]:
    """
    Walk a :class:`click.Command` into the canonical parser tree.

    Mirrors :func:`walk_parser` exactly, same dict shape, so the
    HTML renderer never branches on the source framework. Handles
    both leaf ``Command`` and nested ``Group`` trees; ``--help`` is
    filtered (Click adds it automatically and it has no GUI value).

    Parameters
    ----------
    cmd : click.Command
        A Click command or group. For a Typer app, call
        :func:`sprezzature_cli_gui.schema.walk`, which converts it with
        ``typer.main.get_command`` and then calls this.
    prog : str or None, optional
        Override the ``prog`` field. Defaults to the command's own
        ``name`` (Click sets this from the function name).

    Returns
    -------
    dict
        The canonical parser tree.
    """
    actions: list[dict[str, Any]] = []
    sub_commands: dict[str, dict[str, Any]] = {}
    # ``cmd.params`` are the leaf options / arguments.
    for param in getattr(cmd, "params", []) or []:
        # Click sometimes emits an ``HelpOption`` automatically; we
        # detect it via ``param.is_eager`` + an empty ``name``-shape.
        name: str | None = getattr(param, "name", None)
        if not name or name == "help":
            continue
        actions.append(_serialize_click_param(param))
    # ``Group.commands`` is a dict of sub-commands. Leaf ``Command``
    # objects do not have ``commands``.
    subs: dict[str, Any] = getattr(cmd, "commands", {}) or {}
    for name, sub in subs.items():
        sub_commands[name] = walk_click(sub, prog=name)
    return {
        "prog": prog or getattr(cmd, "name", "cli") or "cli",
        "description": (getattr(cmd, "help", "") or "").strip(),
        "actions": actions,
        "sub_commands": sub_commands,
    }
