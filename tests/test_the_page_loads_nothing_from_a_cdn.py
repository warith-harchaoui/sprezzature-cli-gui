"""
A generated page carries the current Tailwind, cut to what it uses.

The page used to carry ``<script src="https://cdn.tailwindcss.com">``: every
visitor's browser asked a third party for Tailwind, compiled it in the
browser, and lost its styling offline. The generator now takes the full
current release (its standalone CLI, cached) and compiles only the
utilities the page uses into the page's ``<style>``. These tests fake the
CDN and the CLI download; ``conftest.py`` provides a stand-in CLI.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import http.client
import io
import json
import re
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

from sprezzature_cli_gui import render_html
from sprezzature_cli_gui import tailwind as tw
from sprezzature_cli_gui.tailwind import TailwindUnavailable

from .conftest import STAND_IN_CLI, install_stand_in

TREE: dict[str, Any] = {
    "prog": "demo",
    "description": "",
    "actions": [
        {
            "dest": "name",
            "flags": ["--name"],
            "kind": "text",
            "default": "world",
            "required": False,
            "help": "Who to greet",
            "choices": None,
        }
    ],
    "sub_commands": {},
}


class _FakeResponse(io.BytesIO):
    """What ``urlopen`` returns: a body plus the URL after redirects."""

    def __init__(self, url: str, body: bytes = b"") -> None:
        """Hold the final URL and the body.

        Parameters
        ----------
        url : str
            The URL the redirects ended on.
        body : bytes, optional
            The body.
        """
        super().__init__(body)
        self._url = url

    def geturl(self) -> str:
        """Return the URL the redirects ended on.

        Returns
        -------
        str
            The final URL.
        """
        return self._url


@pytest.fixture
def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty cache, the network allowed, the per-process memo cleared.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest's temporary directory.
    monkeypatch : pytest.MonkeyPatch
        Sets the environment for one test.

    Returns
    -------
    pathlib.Path
        The cache root.
    """
    monkeypatch.setenv("SPREZZATURE_CLI_GUI_CACHE", str(tmp_path))
    monkeypatch.delenv("SPREZZATURE_CLI_GUI_OFFLINE", raising=False)
    monkeypatch.setattr(tw, "_CURRENT", {})
    return tmp_path


def _gateway_timeout(url: str) -> urllib.error.HTTPError:
    """Build the error urllib raises when GitHub or the CDN answers 504.

    Parameters
    ----------
    url : str
        The URL that was asked for.

    Returns
    -------
    urllib.error.HTTPError
        A 504.
    """
    return urllib.error.HTTPError(url, 504, "Gateway Timeout", Message(), None)


def _network(
    monkeypatch: pytest.MonkeyPatch,
    version: str | None,
    failure: tuple[str, Exception] | None = None,
) -> list[str]:
    """Fake the CDN (naming *version*) and the CLI download; record requests.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Replaces ``urlopen``.
    version : str or None
        The release the CDN names; None makes every request fail.
    failure : tuple of (str, Exception), optional
        Raise this exception for URLs containing this text.

    Returns
    -------
    list of str
        The URLs requested, filled as the code runs.
    """
    calls: list[str] = []

    def urlopen(request: Any, timeout: float) -> _FakeResponse:
        """Answer as cdn.tailwindcss.com and GitHub do.

        Parameters
        ----------
        request : urllib.request.Request
            The request.
        timeout : float
            Ignored.

        Returns
        -------
        _FakeResponse
            The redirect target, or the CLI.

        Raises
        ------
        urllib.error.URLError
            When *version* is None.
        """
        calls.append(request.full_url)
        if version is None:
            raise urllib.error.URLError("no network")
        if failure is not None and failure[0] in request.full_url:
            raise failure[1]
        if request.full_url == tw.CDN:
            return _FakeResponse(f"{tw.CDN}/{version}")
        import sys

        return _FakeResponse(request.full_url, f"#!{sys.executable}\n{STAND_IN_CLI}".encode())

    monkeypatch.setattr(tw.urllib.request, "urlopen", urlopen)
    return calls


def test_the_page_references_no_external_script_or_stylesheet() -> None:
    """Nothing in the page points at another host, and no Play build is in it."""
    html = render_html(TREE)
    assert re.findall(r'(?:src|href)="(?:https?:)?//', html) == []
    assert "<!-- Tailwind 0.0.1: only the utilities this page uses" in html
    assert "tailwind.config" not in html


def test_only_the_classes_in_use_are_compiled() -> None:
    """The stylesheet holds the page's classes, plus those of extra content."""
    html = render_html(TREE, extra_content=['<div class="only-in-a-script"></div>'])
    style = html[html.index("<style>\n/*stand-in*/") : html.index("</style>")]
    assert ".bg-brand-blue{}" in style
    assert ".only-in-a-script{}" in style
    assert ".grid-cols-12{}" not in style


def test_the_compiler_receives_the_theme_and_media_dark_mode(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The colour tokens and the dark-mode rule reach the Tailwind config.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache, filled with the stand-in.
    monkeypatch : pytest.MonkeyPatch
        Asks the stand-in to record the config it receives.
    """
    install_stand_in(cache)
    record = cache / "received.json"
    monkeypatch.setenv("STAND_IN_RECORD", str(record))
    sheet = tw.stylesheet(["<p class='x'></p>"], offline=True)
    assert sheet.version == "0.0.1"
    received = json.loads(record.read_text())
    assert received["darkMode"] == "media"
    assert received["theme"] == tw.THEME
    assert "brand" in received["theme"]["extend"]["colors"]


def test_the_current_release_is_downloaded_once_and_used(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CDN names the release; its CLI is downloaded once, then cached.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network.
    """
    calls = _network(monkeypatch, "3.9.2")
    first = tw.stylesheet(["<p class='a'></p>"])
    second = tw.stylesheet(["<p class='b'></p>"])
    assert (first.version, second.version) == ("3.9.2", "3.9.2")
    assert calls[0] == tw.CDN
    downloads = [c for c in calls if c.startswith(tw.CLI_RELEASES)]
    assert downloads == [f"{tw.CLI_RELEASES}/v3.9.2/{tw.cli_name()}"]
    assert (cache / "tailwind" / f"3.9.2-{tw.cli_name()}").exists()


def test_without_network_the_newest_cached_release_is_used(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Offline, 3.10.0 wins over 3.9.0: versions compare as numbers.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Cuts the network.
    """
    install_stand_in(cache, "3.9.0")
    install_stand_in(cache, "3.10.0")
    _network(monkeypatch, None)
    assert tw.stylesheet(["<p class='a'></p>"]).version == "3.10.0"


def test_offline_does_not_touch_the_network(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--offline reads the cache and never asks the network.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network, to see whether it is asked.
    """
    install_stand_in(cache, "3.4.17")
    calls = _network(monkeypatch, "9.9.9")
    assert tw.stylesheet(["<p class='a'></p>"], offline=True).version == "3.4.17"
    assert calls == []


def test_no_network_and_an_empty_cache_says_what_to_do(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The error names the cache and asks for one connected run.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Cuts the network.
    """
    _network(monkeypatch, None)
    with pytest.raises(TailwindUnavailable, match="network connection") as caught:
        render_html(TREE)
    assert str(cache / "tailwind") in str(caught.value)
    assert tw.CDN in str(caught.value)


@pytest.mark.parametrize("where", ["releases/download", "cdn.tailwindcss.com"])
def test_a_504_is_reported_as_a_504_and_not_as_no_network(
    cache: Path, monkeypatch: pytest.MonkeyPatch, where: str
) -> None:
    """The network works and a server failed: the message says that.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network.
    where : str
        Which of the two requests answers 504.
    """
    _network(monkeypatch, "3.9.2", failure=(where, _gateway_timeout(where)))
    with pytest.raises(TailwindUnavailable) as caught:
        tw.stylesheet(["<p class='a'></p>"])
    message = str(caught.value)
    assert "HTTP 504" in message
    assert where in message
    assert "network connection" not in message


def test_a_download_cut_off_midway_is_reported_too(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dropped connection is no ``OSError``; it must not escape as a traceback.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network.
    """
    dropped = http.client.IncompleteRead(b"partial", 40_000_000)
    _network(monkeypatch, "3.9.2", failure=("releases/download", dropped))
    with pytest.raises(TailwindUnavailable, match="releases/download"):
        tw.stylesheet(["<p class='a'></p>"])
    assert tw.cached_versions() == []


def test_a_504_with_something_cached_still_compiles(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cause only matters when nothing can replace the download.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network.
    """
    install_stand_in(cache, "3.4.1")
    failure = ("releases/download", _gateway_timeout("releases/download"))
    _network(monkeypatch, "3.9.2", failure=failure)
    assert tw.stylesheet(["<p class='a'></p>"]).version == "3.4.1"


def test_offline_with_an_empty_cache_says_offline(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--offline on an empty cache: one sentence, and the network never asked.

    Parameters
    ----------
    cache : pathlib.Path
        Fixture: an empty cache.
    monkeypatch : pytest.MonkeyPatch
        Fakes the network, to see whether it is asked.
    """
    from click.testing import CliRunner

    from sprezzature_cli_gui.cli import main

    calls = _network(monkeypatch, "9.9.9")
    result = CliRunner().invoke(main, ["argparse:ArgumentParser", "--offline"])
    assert result.exit_code == 1
    assert "--offline" in result.output
    assert calls == []


@pytest.mark.parametrize(
    ("system", "machine", "name"),
    [
        ("Darwin", "arm64", "tailwindcss-macos-arm64"),
        ("Linux", "x86_64", "tailwindcss-linux-x64"),
        ("Linux", "aarch64", "tailwindcss-linux-arm64"),
        ("Windows", "AMD64", "tailwindcss-windows-x64.exe"),
        ("Plan9", "x86_64", None),
    ],
)
def test_the_cli_asset_is_named_as_tailwind_publishes_it(
    system: str, machine: str, name: str | None
) -> None:
    """Each platform maps to its release asset, or to None.

    Parameters
    ----------
    system : str
        ``platform.system()``.
    machine : str
        ``platform.machine()``.
    name : str or None
        The expected asset.
    """
    assert tw.cli_name(system, machine) == name
