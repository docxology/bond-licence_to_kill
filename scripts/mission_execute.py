"""ROGUE mission CLI — execute phase.

Runs the deterministic ROGUE analysis, persists the tagged MissionOutcome to
``output/data/mission_outcome.json``, prints a human summary, and exits 0.
"""

from __future__ import annotations

from _bootstrap import OUTPUT, PROVIDER
from bond_api.serialization import to_json


def main() -> int:
    brief = PROVIDER.brief()
    plan = PROVIDER.plan(brief)
    outcome = PROVIDER.execute(plan)
    serialised = to_json(outcome)
    (OUTPUT / "data").mkdir(parents=True, exist_ok=True)
    (OUTPUT / "data" / "mission_outcome.json").write_text(serialised, encoding="utf-8")
    print(
        f"ROGUE execute: success={outcome.success} steps={outcome.results['steps_completed']} "
        f"input_hash={outcome.provenance.input_hash[:12]}…"
    )
    print(serialised)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
