"""ROGUE mission CLI — debrief phase.

Drives the full five-stage flow (brief → recon → plan → execute → debrief) and
prints the Debrief as tagged JSON with its lessons, then exits 0.
"""

from __future__ import annotations

import sys

from _bootstrap import PROVIDER
from bond_api.protocol import ReconRequest, run_mission
from bond_api.serialization import to_json


def main() -> int:
    goal = sys.argv[1] if len(sys.argv) > 1 else "complete the ROGUE mission"
    debrief = run_mission(PROVIDER, ReconRequest(goal=goal))
    print(to_json(debrief))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
