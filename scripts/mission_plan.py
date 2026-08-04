"""ROGUE mission CLI — plan phase.

Prints the deterministic MissionPlan as tagged JSON and exits 0.
"""

from __future__ import annotations

from _bootstrap import PROVIDER
from bond_api.serialization import to_json


def main() -> int:
    brief = PROVIDER.brief()
    plan = PROVIDER.plan(brief)
    print(to_json(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
