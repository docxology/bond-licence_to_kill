"""Shared test bootstrap for the ROGUE mission.

Pins the headless matplotlib backend (Agg) so figure tests never open a
display window, and puts the repo root + ``src/`` on ``sys.path`` so the
package imports without relying on the installer's editable hook.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
