"""
sprezzature_cli_gui.tailwind
============================

The Tailwind a generated page carries: the current release, cut down to the
utilities the page uses.

What this module does
    :func:`stylesheet` does two steps on every generation. It takes the full
    Tailwind of the current release (the standalone CLI, which holds every
    utility), then compiles from it only the utilities that appear in the
    page. The renderer puts that CSS, about 10 kB, in the page's ``<style>``.
    The page therefore loads nothing when it is opened: the visitor's browser
    never contacts a third party, and the page styles itself offline.

Which release
    The one Tailwind's Play CDN currently serves. ``https://cdn.tailwindcss.com``
    answers with a redirect to it, e.g. ``/3.4.17``; that path is the version,
    read without downloading the script. One request per process.

Where the CLI comes from
    Tailwind's GitHub release of that version, one binary per platform
    (about 45 MB), downloaded once into the cache.

When the network is missing
    The newest release whose CLI is already cached is used. ``offline=True``
    (the command line's ``--offline``) skips the network on purpose. With
    nothing cached, :class:`TailwindUnavailable` says what actually happened:
    an HTTP status from a server that answered is not an absent network, and
    the advice for one would be wrong for the other.

Where the cache lives
    ``SPREZZATURE_CLI_GUI_CACHE`` when set, else ``$XDG_CACHE_HOME`` or
    ``~/.cache``, under ``sprezzature-cli-gui/tailwind/``.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import http.client
import json
import os
import platform
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

#: The Play CDN's entry point; it redirects to the current release.
CDN = "https://cdn.tailwindcss.com"

#: Where the standalone CLI of each release is published.
CLI_RELEASES = "https://github.com/tailwindlabs/tailwindcss/releases/download"

#: How long one generation waits for the CDN's answer.
TIMEOUT_SECONDS = 10.0

#: How long one generation waits for the CLI download (about 45 MB).
CLI_TIMEOUT_SECONDS = 180.0

#: What a fetch can raise. ``URLError``, ``HTTPError`` and timeouts are
#: ``OSError``; a connection dropped mid-body is an ``HTTPException`` and is not.
_FETCH_ERRORS = (OSError, http.client.HTTPException)

#: The sprezzature-ui semantic colour tokens the page's classes name. An
#: unknown token compiles to nothing (the "Build command" button once went
#: white on transparent), so the compiled CSS must know them. Values match
#: sprezzature-ui's stack-tailwind.md.
THEME: dict[str, object] = {
    "extend": {
        "colors": {
            "brand": {
                "blue": {"DEFAULT": "#0088FF", "dark": "#0091FF"},
                "red": {"DEFAULT": "#FF383C", "dark": "#FF4245"},
            },
            "label": {
                "primary": "#000000",
                "primary-dark": "#FFFFFF",
                "secondary": "rgba(60,60,67,0.6)",
                "secondary-dark": "rgba(235,235,245,0.6)",
            },
            "surface": {"secondary": "#F2F2F7", "secondary-dark": "#1C1C1E"},
            "separator": "rgba(60,60,67,0.36)",
        }
    }
}

_VERSION = re.compile(r"/(\d+\.\d+\.\d+)$")

#: One question to the CDN per process: twenty pages in one run ask once.
_CURRENT: dict[str, str] = {}


class TailwindUnavailable(RuntimeError):
    """No CLI can be had (the message says why), or the one cached fails."""


@dataclass(frozen=True)
class Stylesheet:
    """The CSS compiled for one page.

    Parameters
    ----------
    version : str
        The Tailwind release it was compiled with, e.g. ``"3.4.17"``.
    css : str
        Minified CSS holding only the utilities the page uses.
    """

    version: str
    css: str


def cache_dir() -> Path:
    """Return the directory releases are kept in, creating it.

    Returns
    -------
    pathlib.Path
        The cache directory.
    """
    base = os.environ.get("SPREZZATURE_CLI_GUI_CACHE")
    if base:
        folder = Path(base)
    else:
        root = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
        folder = Path(root) / "sprezzature-cli-gui"
    folder = folder / "tailwind"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _offline(offline: bool) -> bool:
    """Say whether the network is off, by argument or environment.

    Parameters
    ----------
    offline : bool
        The caller's choice.

    Returns
    -------
    bool
        True when ``offline`` or ``SPREZZATURE_CLI_GUI_OFFLINE=1``.
    """
    return offline or os.environ.get("SPREZZATURE_CLI_GUI_OFFLINE") == "1"


def _why(url: str, exc: Exception) -> str:
    """Say what went wrong fetching a URL, keeping a status apart from no network.

    Parameters
    ----------
    url : str
        What was being fetched.
    exc : Exception
        One of :data:`_FETCH_ERRORS`.

    Returns
    -------
    str
        A clause naming the URL and the cause, with the advice that fits it.
    """
    if isinstance(exc, urllib.error.HTTPError):
        answer = f"{url} answered HTTP {exc.code} ({exc.reason})"
        if exc.code >= 500:
            return f"{answer}: that server is failing, not your connection, so try again later"
        return answer
    if isinstance(exc, urllib.error.URLError):
        return f"{url} could not be reached ({exc.reason}); run once with a network connection"
    if isinstance(exc, TimeoutError):
        return f"{url} did not answer in time; run once with a working network connection"
    return f"fetching {url} failed ({exc!r})"


def _version_key(version: str) -> tuple[int, ...]:
    """Order releases numerically, so 3.10.0 sorts after 3.9.0.

    Parameters
    ----------
    version : str
        ``major.minor.patch``.

    Returns
    -------
    tuple of int
        The three numbers.
    """
    return tuple(int(part) for part in version.split("."))


def cli_name(system: str | None = None, machine: str | None = None) -> str | None:
    """Name the standalone CLI asset for a platform, as Tailwind's releases do.

    Parameters
    ----------
    system : str, optional
        ``platform.system()``; this machine's when None.
    machine : str, optional
        ``platform.machine()``; this machine's when None.

    Returns
    -------
    str or None
        E.g. ``"tailwindcss-macos-arm64"``; None for a platform Tailwind
        publishes no binary for.
    """
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}.get(machine)
    os_name = {"darwin": "macos", "linux": "linux", "windows": "windows"}.get(system)
    if arch is None or os_name is None:
        return None
    return f"tailwindcss-{os_name}-{arch}" + (".exe" if os_name == "windows" else "")


def cached_versions() -> list[str]:
    """List the releases whose CLI for this platform is cached, newest first.

    Returns
    -------
    list of str
        Versions.
    """
    name = cli_name()
    if name is None:
        return []
    pattern = re.compile(rf"^(\d+\.\d+\.\d+)-{re.escape(name)}$")
    found = [m.group(1) for p in cache_dir().iterdir() if (m := pattern.match(p.name))]
    return sorted(found, key=_version_key, reverse=True)


def current_version(timeout: float = TIMEOUT_SECONDS) -> str:
    """Ask the Play CDN which release it serves now.

    Parameters
    ----------
    timeout : float, optional
        Seconds to wait.

    Returns
    -------
    str
        The release, e.g. ``"3.4.17"``.

    Raises
    ------
    OSError
        When the CDN cannot be reached or redirects to a path naming no
        release.
    """
    if "version" in _CURRENT:
        return _CURRENT["version"]
    request = urllib.request.Request(
        CDN, method="HEAD", headers={"User-Agent": "sprezzature-cli-gui"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        final = response.geturl()
    match = _VERSION.search(final)
    if match is None:
        raise OSError(f"{CDN} redirected to {final}, which names no release")
    _CURRENT["version"] = match.group(1)
    return _CURRENT["version"]


def cli(version: str, offline: bool = False) -> Path | None:
    """Return the standalone CLI of a release, downloading it once.

    Parameters
    ----------
    version : str
        The release, e.g. ``"3.4.17"``.
    offline : bool, optional
        Use the cache only.

    Returns
    -------
    pathlib.Path or None
        The executable, or None when it is not cached and *offline* forbids
        downloading it.

    Raises
    ------
    TailwindUnavailable
        When the download fails; the message says how.
    """
    name = cli_name()
    if name is None:
        return None
    target = cache_dir() / f"{version}-{name}"
    if target.exists():
        return target
    if _offline(offline):
        return None
    url = f"{CLI_RELEASES}/v{version}/{name}"
    request = urllib.request.Request(url, headers={"User-Agent": "sprezzature-cli-gui"})
    partial = target.with_name(target.name + ".part")
    try:
        with urllib.request.urlopen(request, timeout=CLI_TIMEOUT_SECONDS) as response:  # noqa: S310
            partial.write_bytes(response.read())
    except _FETCH_ERRORS as exc:
        partial.unlink(missing_ok=True)
        raise TailwindUnavailable(_why(url, exc)) from exc
    partial.chmod(0o755)
    partial.replace(target)
    return target


def _resolve(offline: bool) -> tuple[str, Path]:
    """Pick the release and its CLI: the current one, else the newest cached.

    Parameters
    ----------
    offline : bool
        Skip the network.

    Returns
    -------
    str, pathlib.Path
        The version and its executable.

    Raises
    ------
    TailwindUnavailable
        When no CLI is cached and none can be downloaded. The message says
        what stopped the download.
    """
    if cli_name() is None:
        raise TailwindUnavailable(
            f"Tailwind publishes no CLI for {platform.system()} {platform.machine()}"
        )
    cause = (
        "the network is switched off (--offline or SPREZZATURE_CLI_GUI_OFFLINE=1); "
        "run once with a network connection"
    )
    if not _offline(offline):
        try:
            version = current_version()
        except _FETCH_ERRORS as exc:
            cause = _why(CDN, exc)
        else:
            try:
                executable = cli(version)
            except TailwindUnavailable as exc:
                cause = str(exc)
            else:
                if executable is not None:
                    return version, executable
    for cached in cached_versions():
        executable = cli(cached, offline=True)
        if executable is not None:
            return cached, executable
    raise TailwindUnavailable(f"no Tailwind CLI is cached in {cache_dir()} and {cause}")


def stylesheet(texts: Sequence[str], offline: bool = False) -> Stylesheet:
    """Compile, with the current Tailwind, only the utilities some text uses.

    Parameters
    ----------
    texts : sequence of str
        The page's markup, and any script that adds classes to it later.
    offline : bool, optional
        Use the newest cached CLI without asking the network.

    Returns
    -------
    Stylesheet
        The release used and the minified CSS.

    Raises
    ------
    TailwindUnavailable
        When no CLI can be had, or the CLI fails.
    """
    version, executable = _resolve(offline)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for i, text in enumerate(texts):
            (folder / f"content-{i}.html").write_text(text, encoding="utf-8")
        config = {
            "content": [(folder / "content-*.html").as_posix()],
            "darkMode": "media",
            "theme": THEME,
        }
        (folder / "tailwind.config.js").write_text(
            "module.exports = " + json.dumps(config) + ";\n", encoding="utf-8"
        )
        (folder / "input.css").write_text(
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
            encoding="utf-8",
        )
        out = folder / "out.css"
        try:
            done = subprocess.run(
                [
                    str(executable),
                    "--config",
                    str(folder / "tailwind.config.js"),
                    "--input",
                    str(folder / "input.css"),
                    "--output",
                    str(out),
                    "--minify",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TailwindUnavailable(f"Tailwind {version} CLI failed: {exc}") from exc
        if done.returncode != 0 or not out.exists():
            raise TailwindUnavailable(f"Tailwind {version} CLI failed: {done.stderr.strip()}")
        return Stylesheet(version, out.read_text(encoding="utf-8").strip())
