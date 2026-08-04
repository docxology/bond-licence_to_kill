"""Shared thin-script bootstrap for the ROGUE mission CLIs.

Every ``scripts/*.py`` first imports from here so that the repo root and
``src/`` are on ``sys.path`` (the package is not a workspace member) and a
single canonical provider instance is available to every phase CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT), str(ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from licence_to_kill.mission import MissionProvider  # noqa: E402

#: Canonical provider instance shared by the phase CLIs.
PROVIDER = MissionProvider()
#: Absolute output root (regenerable, git-ignored).
OUTPUT = ROOT / "output"
