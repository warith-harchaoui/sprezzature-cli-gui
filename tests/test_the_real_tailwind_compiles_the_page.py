"""
The real Tailwind CLI, on a real page.

Everything else in the suite compiles with a stand-in that writes one empty
rule per class: it cannot see a colour token that compiles to nothing, a dark
variant in the wrong strategy, or a flag the real CLI refuses. That code
shipped once without the real binary ever having run.

Where these run
    In the ``real-tailwind`` job of ``.github/workflows/ci.yml``, with
    ``SPREZZATURE_CLI_GUI_REQUIRE_REAL_TAILWIND=1``: the CLI is downloaded for
    real, and failing to get it fails the job. On a machine, whenever a real
    generation has cached the CLI. Otherwise they skip, and the reason says
    so; :func:`test_the_real_compile_is_wired_into_ci` keeps the job from
    quietly disappearing, which would leave nothing but the skip.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

from sprezzature_cli_gui import render_html
from sprezzature_cli_gui import tailwind as tw

from .conftest import REAL_CACHE, STAND_IN_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent

#: With this set to 1 the CLI is downloaded, and not having it is a failure.
REQUIRE = "SPREZZATURE_CLI_GUI_REQUIRE_REAL_TAILWIND"

TREE: dict[str, Any] = {
    "prog": "demo",
    "description": "A demo",
    "actions": [
        {
            "dest": "verbose",
            "flags": ["--verbose"],
            "kind": "bool",
            "default": False,
            "required": False,
            "help": "Say more",
            "choices": None,
        },
        {
            "dest": "name",
            "flags": ["--name"],
            "kind": "text",
            "default": "world",
            "required": True,
            "help": "Who to greet",
            "choices": None,
        },
    ],
    "sub_commands": {
        "convert": {
            "prog": "demo convert",
            "description": "Convert",
            "actions": [
                {
                    "dest": "fmt",
                    "flags": ["--fmt"],
                    "kind": "choice",
                    "default": "csv",
                    "required": False,
                    "help": "Format",
                    "choices": ["csv", "json"],
                }
            ],
            "sub_commands": {},
        }
    },
}


@pytest.fixture
def real_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the generator at the real CLI, or say why it cannot run here.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Undoes the suite's stand-in for one test.
    """
    if REAL_CACHE:
        monkeypatch.setenv("SPREZZATURE_CLI_GUI_CACHE", REAL_CACHE)
    else:
        monkeypatch.delenv("SPREZZATURE_CLI_GUI_CACHE", raising=False)
    monkeypatch.setattr(tw, "_CURRENT", {})
    if os.environ.get(REQUIRE) == "1":
        monkeypatch.delenv("SPREZZATURE_CLI_GUI_OFFLINE", raising=False)
    elif not tw.cached_versions():
        pytest.skip(
            f"NOT RUN HERE: no real Tailwind CLI in {tw.cache_dir()}. These run in the "
            "real-tailwind job of .github/workflows/ci.yml, and here once one real "
            "`sprezzature-cli-gui` generation has cached the CLI."
        )


def _page(extra: tuple[str, ...] = ()) -> tuple[str, str]:
    """Render the demo page with the real CLI.

    Parameters
    ----------
    extra : tuple of str, optional
        ``extra_content``.

    Returns
    -------
    tuple of str
        The page and the compiled CSS in it.
    """
    html = render_html(TREE, extra_content=extra)
    assert f"Tailwind {STAND_IN_VERSION}" not in html, "this is the stand-in, not the real CLI"
    start = html.index("<style>\n") + len("<style>\n")
    return html, html[start : html.index("</style>", start)]


def _selector(name: str) -> str:
    """Write a class name as it appears in the compiled CSS.

    Parameters
    ----------
    name : str
        The class, e.g. ``dark:bg-surface-secondary-dark``.

    Returns
    -------
    str
        The escaped selector, e.g. ``.dark\\:bg-surface-secondary-dark``.
    """
    return "." + re.sub(r"([:\[\]/.%(),#])", r"\\\1", name)


def _rule(css: str, name: str) -> str:
    """Return the declarations compiled for a class.

    Parameters
    ----------
    css : str
        The compiled stylesheet.
    name : str
        The class.

    Returns
    -------
    str
        What is between the braces.
    """
    match = re.search(re.escape(_selector(name)) + r"\{([^}]*)\}", css)
    assert match is not None, f"{name} was not compiled"
    return match.group(1)


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
def test_every_class_on_the_page_has_a_rule() -> None:
    """A class that compiles to nothing is how the button went invisible."""
    html, css = _page()
    classes = {c for value in re.findall(r'class="([^"]*)"', html) for c in value.split()}
    assert len(classes) > 30, "the page should use many utilities"
    assert [c for c in sorted(classes) if _selector(c) not in css] == []


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("bg-brand-blue", "rgb(0 136 255"),
        ("text-label-secondary", "rgba(60,60,67,.6)"),
        ("border-separator", "rgba(60,60,67,.36)"),
        ("dark:bg-surface-secondary-dark", "rgb(28 28 30"),
        ("dark:text-label-secondary-dark", "rgba(235,235,245,.6)"),
    ],
)
def test_the_theme_tokens_compile_to_their_values(name: str, value: str) -> None:
    """The semantic tokens exist only through the theme handed to the CLI.

    Parameters
    ----------
    name : str
        A class the page uses.
    value : str
        The colour it must compile to.
    """
    _, css = _page()
    assert value in _rule(css, name)


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
def test_dark_mode_follows_the_system() -> None:
    """Dark variants live under the media query, as they did with the Play CDN."""
    _, css = _page()
    opening = css.index("@media (prefers-color-scheme:dark)")
    assert css.index(_selector("dark:bg-black")) > opening
    assert ".dark " not in css


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
def test_only_what_the_page_uses_is_compiled() -> None:
    """The base styles are there, an unused utility is not, the size stays small."""
    _, css = _page()
    assert "box-sizing:border-box" in css
    assert _selector("grid-cols-12") not in css
    assert len(css) < 30_000


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
def test_extra_content_is_compiled() -> None:
    """A class only a caller's script names still gets its rule."""
    _, css = _page(('<div class="grid-cols-12"></div>',))
    assert _selector("grid-cols-12") in css


@pytest.mark.real_tailwind
@pytest.mark.usefixtures("real_cli")
def test_the_page_loads_nothing() -> None:
    """No script or link leaves the file, and the CSS imports nothing."""
    html, css = _page()
    assert re.findall(r'(?:src|href)="', html) == []
    assert "@import" not in css
    assert "url(http" not in css


def test_the_real_compile_is_wired_into_ci() -> None:
    """The skip above is only honest while a job takes the other branch."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    job = workflow[workflow.index("  real-tailwind:") :]
    job = job[: job.index("\n  floor:")]
    assert f'{REQUIRE}: "1"' in job
    assert "pytest -q -m real_tailwind" in job
    assert "\n    if:" not in job and "continue-on-error" not in job
