"""ROGUE mission CLI — brief phase.

Prints the frozen MissionBrief for the licence_to_kill film as deterministic
tagged JSON (bond-api serialization) and exits 0.
"""

from __future__ import annotations

from _bootstrap import PROVIDER
from bond_api.serialization import to_json


def main() -> int:
    print(to_json(PROVIDER.brief()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
