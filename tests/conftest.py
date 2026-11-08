"""
Keep the test suite off the network: pages compile with a stand-in Tailwind CLI.

Rendering a page takes the current Tailwind release and its standalone CLI,
downloaded from the network. The suite would then depend on the network,
and run a 45 MB binary, so it points the cache at a temporary folder holding
a stand-in CLI and switches the network off. The stand-in does what the
real CLI does that the tests can see: it reads the config's content files
and writes one rule per class it finds, and it records the config it was
given. Only ``tests/test_the_real_tailwind_compiles_the_page.py`` runs the
real one.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from sprezzature_cli_gui.tailwind import cli_name

#: Where the real CLI is cached for whoever runs the suite, read before the
#: fixture below points the cache at the stand-in.
REAL_CACHE = os.environ.get("SPREZZATURE_CLI_GUI_CACHE")

#: The release the stand-in CLI claims to be.
STAND_IN_VERSION = "0.0.1"

#: The stand-in CLI: a Python script with the real one's arguments.
STAND_IN_CLI = """\
import glob, json, os, re, sys
args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
source = open(args["--config"]).read()
config = json.loads(source[len("module.exports = "):].rstrip().rstrip(";"))
if os.environ.get("STAND_IN_RECORD"):
    open(os.environ["STAND_IN_RECORD"], "w").write(json.dumps(config))
names = set()
for pattern in config["content"]:
    for path in glob.glob(pattern):
        for value in re.findall(r'class(?:Name)?\\s*=\\s*"([^"]*)"', open(path).read()):
            names.update(value.split())
css = "/*stand-in*/" + "".join("." + n.replace(":", "\\\\:") + "{}" for n in sorted(names))
open(args["--output"], "w").write(css)
"""


def install_stand_in(root: Path, version: str = STAND_IN_VERSION) -> Path:
    """Write the stand-in CLI into a cache root, as the real one is cached.

    Parameters
    ----------
    root : pathlib.Path
        The cache root (``SPREZZATURE_CLI_GUI_CACHE``).
    version : str, optional
        The release it is filed under.

    Returns
    -------
    pathlib.Path
        The executable.
    """
    folder = root / "tailwind"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{version}-{cli_name()}"
    target.write_text(f"#!{sys.executable}\n{STAND_IN_CLI}")
    target.chmod(0o755)
    return target


@pytest.fixture(autouse=True, scope="session")
def offline_tailwind(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Point the Tailwind cache at the stand-in CLI and switch the network off.

    Parameters
    ----------
    tmp_path_factory : pytest.TempPathFactory
        Pytest's session-wide temporary folders.

    Yields
    ------
    pathlib.Path
        The cache root the suite uses.
    """
    root = tmp_path_factory.mktemp("cache")
    install_stand_in(root)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("SPREZZATURE_CLI_GUI_CACHE", str(root))
        patch.setenv("SPREZZATURE_CLI_GUI_OFFLINE", "1")
        yield root
