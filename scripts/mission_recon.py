"""ROGUE mission CLI — recon phase.

Runs reconnaissance against the canonical ROGUE assets and prints the
ReconReport as tagged JSON. A goal may be passed as argv[1]; the default is
the mission's stated objective.
"""

from __future__ import annotations

import sys

from _bootstrap import PROVIDER
from bond_api.protocol import ReconRequest
from bond_api.serialization import to_json

_DEFAULT_GOAL = "survey layering, integration, vessel anomaly, and rogue-00 risk posture"


def main() -> int:
    goal = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_GOAL
    report = PROVIDER.recon(ReconRequest(goal=goal))
    print(to_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
